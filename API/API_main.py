import uvicorn
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.openapi.utils import get_openapi
from .schemas import Animal, AnimalResponse, SearchAttr, AnimalEdit, AnimalDetail
from core.manager import AnimalManager, AnimalNotFoundError

app = FastAPI()
manager = AnimalManager()
manager.load_from_file()

def custom_openai():
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

app.openapi = custom_openai

@app.post(
    "/animals",
    response_model=AnimalResponse,
    summary="動物の追加",
    description="種類と名前を入力して動物を追加します")
def add_animal(req: Animal):
    try:
        new_animal = manager.add_animal(animal_type=req.type, name=req.name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    manager.save_to_file()

    return AnimalResponse(
        id=new_animal.id,
        type=new_animal.type_en,
        name=new_animal.name
    )

@app.post(
    "/animals/random",
    response_model=list[AnimalResponse],
    summary="動物をランダムに追加",
    description="指定した回数ランダムに動物を追加します")
def add_random_animal(count: int):
    try:
        added_animals = manager.add_random_animal(count)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    manager.save_to_file()

    return[
        AnimalResponse(
            id=animal.id,
            type=animal.type_en,
            name=animal.name
        ) for animal in added_animals
    ]


@app.delete(
    "/animals/{delete_id}",
    response_model=AnimalResponse,
    summary="動物の削除",
    description="動物を削除します")
def remove_animal(delete_id: int):
    try:
        removed_animal = manager.remove_animal(delete_id)
    except AnimalNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    manager.save_to_file()

    return AnimalResponse(
        id=removed_animal.id,
        type=removed_animal.type_en,
        name=removed_animal.name
    )

@app.patch(
        "/animals/{animal_id}",
        response_model=AnimalDetail,
        summary="動物の属性変更",
        description="動物の属性(種類・名前・特技)を変更します"
)
def edit_animal(animal_id: int, req: AnimalEdit):
    try:
        target_animal = manager.get_animal(animal_id)
        if req.type is not None:
            target_animal = manager.edit_animal_type(animal_id, req.type)
        if req.name is not None:
            target_animal = manager.edit_animal_name(animal_id, req.name)
        if req.ability is not None:
            target_animal = manager.edit_animal_ability(animal_id, req.ability)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except AnimalNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    manager.save_to_file()
    return AnimalDetail(
        id=target_animal.id,
        type=target_animal.type_en,
        name=target_animal.name,
        abilities=target_animal.get_all_ability()
    )


@app.get(
    "/animals",
    response_model=list[AnimalResponse],
    summary="条件に一致する動物listの取得",
    description="検索条件(attr,keyword)を指定して、動物のリストを取得します"
)
def get_animals(attr: SearchAttr, keyword: str = None):
    """
    attr (Query Parameter): 検索対象の属性 (デフォルト: "すべて")
                           "ID", "種類", "名前", "特技" が指定可能
    keyword (Query Parameter): 検索したいキーワード (任意)
    """
    if keyword:
        try:
            animals = manager.search_animal(attr, keyword)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    else:
        animals = manager.get_all_animals()

    return [AnimalResponse(
        id=animal.id,
        type=animal.type_en,
        name=animal.name
        ) for animal in animals]

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)