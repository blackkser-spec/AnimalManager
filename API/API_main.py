import uvicorn
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.openapi.utils import get_openapi
from . import schemas
from core.manager import AnimalManager, AnimalNotFoundError
from core.storage import JsonStorage

app = FastAPI()
storage = JsonStorage("data/animals.json")
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

@app.post(
    "/animals",
    response_model=schemas.AnimalResponse,
    summary="動物の追加",
    description="種類と名前を入力して動物を追加します")
def add_animal(req: schemas.Animal):
    try:
        new_animal = manager.add_animal(animal_type=req.type, name=req.name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not manager.save_to_file():
        raise HTTPException(status_code=500, detail="データの保存に失敗しました")

    return schemas.AnimalResponse(
        id=new_animal.id,
        type=new_animal.type_en,
        name=new_animal.name
    )

@app.post(
    "/animals/random",
    response_model=list[schemas.AnimalResponse],
    summary="動物をランダムに追加",
    description="指定した回数ランダムに動物を追加します")
def add_random_animal(count: int):
    try:
        added_animals = manager.add_random_animal(count)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not manager.save_to_file():
        raise HTTPException(status_code=500, detail="データの保存に失敗しました")

    return [
        schemas.AnimalResponse(
            id=animal.id,
            type=animal.type_en,
            name=animal.name
        ) for animal in added_animals
    ]


@app.delete(
    "/animals/{id}",
    response_model=schemas.AnimalResponse,
    summary="動物の削除",
    description="動物を削除します")
def remove_animal(id: int):
    try:
        removed_animal = manager.remove_animal(id)
    except AnimalNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    if not manager.save_to_file():
        raise HTTPException(status_code=500, detail="データの保存に失敗しました")

    return schemas.AnimalResponse(
        id=removed_animal.id,
        type=removed_animal.type_en,
        name=removed_animal.name
    )

@app.patch(
    "/animals/{id}",
    response_model=schemas.AnimalDetail,
    summary="動物の属性変更",
    description="動物の属性(種類・名前・特技)を変更します"
)
def edit_animal(id: int, req: schemas.AnimalEdit):
    try:
        target_animal = manager.get_animal(id)
        if req.type is not None:
            target_animal = manager.edit_animal_type(id, req.type)
        if req.name is not None:
            target_animal = manager.edit_animal_name(id, req.name)
        if req.ability is not None:
            target_animal = manager.edit_animal_ability(id, req.ability)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except AnimalNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    if not manager.save_to_file():
        raise HTTPException(status_code=500, detail="データの保存に失敗しました")
    return schemas.AnimalDetail(
        id=target_animal.id,
        type=target_animal.type_en,
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
    try:
        animal = manager.get_animal(id)
        return schemas.AnimalDetail(
            id=animal.id,
            type=animal.type_en,
            name=animal.name,
            abilities=animal.get_all_ability()
        )
    except AnimalNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post(
    "/system/reset",
    summary="データリセット",
    description="全てのデータを消去し初期状態に戻します")
def reset_data():
    manager.data_reset()
    if not manager.save_to_file():
        raise HTTPException(status_code=500, detail="データの保存に失敗しました")
    return {"message": "Data has been reset successfully"}


@app.get(
    "/animals/act/{ability}",
    response_model=list[str],
    summary="動物の特技実行",
    description="list内の動物に、指定した特技を実行させます"
)
def act_animal(ability: schemas.AbilityType):  #現状searchと大差ないため後ほど回収予定
    try:
        return manager.act_animal(ability.value)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    

@app.get(
    "/animals",
    response_model=list[schemas.AnimalResponse],
    summary="動物listの取得",
    description="検索条件(attr,keyword)を指定して、動物のリストを取得します"
)
def get_animals(search_attr: schemas.SearchAttr = schemas.SearchAttr.all, keyword: str = None, sort_by: schemas.SortAttr = schemas.SortAttr.id):
    """
    attr (Query Parameter): 検索対象の属性
                           "すべて","ID", "種類", "名前", "特技" が指定可能
    keyword (Query Parameter): 検索したいキーワード (任意)
    """
    animals = manager.get_all_animals()
    try:
        if keyword:
            animals = manager.search_animal(search_attr.value, keyword)
        if sort_by:
            animals = manager.sort_list(animals, sort_by.name)
    except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    return [
        schemas.AnimalResponse(
            id=animal.id,
            type=animal.type_en,
            name=animal.name
        ) for animal in animals
    ]



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)