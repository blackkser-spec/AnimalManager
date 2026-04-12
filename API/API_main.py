import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from . import schemas
from core.manager import AnimalManager, AnimalNotFoundError
from core.animal_repository import AnimalRepository

app = FastAPI()
storage = AnimalRepository("data/animals.json")
manager = AnimalManager(storage)
manager.load_from_file()

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="AnimalManager webAPI",
        version="alpha1.0.0",
        description="学習用のAPIです",
        routes=app.routes
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

@app.exception_handler(IOError)
async def io_error_handler(request: Request, exc: IOError):
    return JSONResponse(status_code=500, content={"detail": str(exc)})

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})

@app.exception_handler(AnimalNotFoundError)
async def not_found_error_handler(request: Request, exc: AnimalNotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})

@app.post(
    "/animals",
    status_code=201,
    response_model=schemas.AnimalResult,
    summary="動物の追加",
    description="種類と名前を入力して動物を追加します")
def add_animal(req: schemas.Animal):
    new_animal = manager.add_animal(animal_type=req.type, name=req.name)
    manager.save_to_file()

    return schemas.AnimalResult(
        id=new_animal.id,
        name=new_animal.name
    )

@app.post(
    "/animals/random",
    status_code=201,
    response_model=list[schemas.AnimalResult],
    summary="動物をランダムに追加",
    description="指定した回数ランダムに動物を追加します")
def add_random_animal(count: int):
    added_animals = manager.add_random_animal(count)
    manager.save_to_file()

    return [
        schemas.AnimalResult(
            id=animal.id,
            name=animal.name
        ) for animal in added_animals
    ]


@app.delete(
    "/animals/{id}",
    response_model=schemas.AnimalResult,
    summary="動物の削除",
    description="動物を削除します")
def remove_animal(id: int):
    removed_animal = manager.remove_animal(id)
    manager.save_to_file()

    return schemas.AnimalResult(
        id=removed_animal.id,
        name=removed_animal.name
    )

@app.patch(
    "/animals/{id}",
    response_model=schemas.AnimalDetail,
    summary="動物の属性変更",
    description="動物の属性(種類・名前・特技)を変更します"
)
def edit_animal(id: int, req: schemas.AnimalEdit):
    update_data = req.model_dump(exclude_unset=True)
    
    target_animal = manager.get_animal(id)
    for attr, value in update_data.items():
        target_animal = manager.edit_animal(id, attr, value)

    manager.save_to_file()
    return schemas.AnimalDetail(
        id=target_animal.id,
        type_en=target_animal.type_en,
        type_jp=target_animal.type_jp,
        name=target_animal.name,
        abilities=target_animal.get_all_ability()
    )

@app.get(
    "/animals/types",
    response_model=list[str],
    summary="動物の種類一覧取得",
    description="登録可能な動物の種類一覧を取得します")
def get_animal_types():
    return manager.get_available_animal_types()

@app.get(
    "/animals/abilities",
    response_model=list[str],
    summary="特技一覧取得",
    description="登録可能な特技の一覧を取得します")
def get_abilities():
    return manager.get_available_abilities()

@app.get(
    "/animals/{id}",
    response_model=schemas.AnimalDetail,
    summary="動物の詳細取得",
    description="指定したIDの動物の詳細情報を取得します"
)
def get_animal(id: int):
    animal = manager.get_animal(id)
    return schemas.AnimalDetail(
        id=animal.id,
        type_en=animal.type_en,
        type_jp=animal.type_jp,
        name=animal.name,
        abilities=animal.get_all_ability()
    )
    
@app.get(
    "/animals",
    response_model=list[schemas.AnimalDetail],
    summary="動物listの取得",
    description="検索条件(attr,keyword)を指定して、動物のリストを取得します"
)
def search_animal(search_attr: schemas.SearchAttr = schemas.SearchAttr.all, keyword: str = None, sort_by: schemas.SortAttr = schemas.SortAttr.id):
    """
    attr (Query Parameter): 検索対象の属性
    "すべて","ID", "種類", "名前", "特技" が指定可能
    keyword (Query Parameter): 検索したいキーワード (任意)
    """
    animals = manager.get_all_animals()
    if keyword:
        animals = manager.search_animal(search_attr.value, keyword)
    if sort_by:
        animals = manager.sort_list(animals, sort_by.name)

    return [
        schemas.AnimalDetail(
            id=animal.id,
            type_en=animal.type_en,
            type_jp=animal.type_jp,
            name=animal.name,
            abilities=animal.get_all_ability()
        ) for animal in animals
    ]

@app.get(
    "/animals/act/{ability}",
    response_model=list[str],
    summary="動物の特技実行",
    description="list内の動物に、指定した特技を実行させます"
)
def act_animal(ability: schemas.AbilityType):  #現状searchと大差ないため後ほど回収予定
    return manager.act_animal(ability.value)

@app.post(
    "/system/reset",
    summary="データリセット",
    description="全てのデータを消去し初期状態に戻します")
def reset_data():
    manager.data_clear()
    manager.save_to_file()
    return {"message": "Data has been reset successfully"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)