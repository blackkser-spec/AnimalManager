import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from . import schemas
from core.manager import AnimalManager
from core.exceptions import ValidationError, AnimalNotFoundError, SaveError
from core.animal_repository import AnimalRepository
from api.exceptions import BadRequest, NotFound, InternalServerError


app = FastAPI()
storage = AnimalRepository("data/animals.json")
manager = AnimalManager(storage)
manager.load_from_file()

def custom_openapi() -> dict:
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

def format_error_response(exc: Exception) -> dict:
    return {
        "key": exc.key,
        "details": exc.details
    }


@app.exception_handler(InternalServerError)
async def io_error_handler(request: Request, exc: InternalServerError):
    return JSONResponse(status_code=500, content=format_error_response(exc))

@app.exception_handler(BadRequest)
async def value_error_handler(request: Request, exc: BadRequest):
    return JSONResponse(status_code=400, content=format_error_response(exc))

@app.exception_handler(NotFound)
async def not_found_error_handler(request: Request, exc: NotFound):
    return JSONResponse(status_code=404, content=format_error_response(exc))

@app.exception_handler(SaveError)
async def save_error_handler(request, exc):
    return JSONResponse(status_code=500, content=format_error_response(InternalServerError(exc.key, **exc.kwargs)))

@app.post(
    "/animals",
    status_code=201,
    response_model=schemas.AnimalResult,
    summary="動物の追加",
    description="種類と名前を入力して動物を追加します")
def add_animal(req: schemas.Animal) -> schemas.AnimalResult:
    try:
        new_animal = manager.add_animal(animal_type=req.animal_type, name=req.name)
    except ValidationError as e:
        raise BadRequest(e.key, **e.kwargs)
    manager.save_to_file()

    return schemas.AnimalResult(
        id=new_animal.id,
        animal_type=new_animal.animal_type,
        name=new_animal.name
    )

@app.post(
    "/animals/random",
    status_code=201,
    response_model=list[schemas.AnimalResult],
    summary="動物をランダムに追加",
    description="指定した回数ランダムに動物を追加します")
def add_random_animal(count: int) -> list[schemas.AnimalResult]:
    try:
        added_animals = manager.add_random_animal(count)
    except ValidationError as e:
        raise BadRequest(e.key, **e.kwargs)
    manager.save_to_file()

    return [
        schemas.AnimalResult(
            id=animal.id,
            animal_type=animal.animal_type,
            name=animal.name
        ) for animal in added_animals
    ]


@app.delete(
    "/animals/{id}",
    response_model=schemas.AnimalResult,
    summary="動物の削除",
    description="動物を削除します")
def remove_animal(id: int) -> schemas.AnimalResult:
    try:
        removed_animal = manager.remove_animal(id)
    except AnimalNotFoundError as e:
        raise NotFound(e.key, **e.kwargs)
    except ValidationError as e:
        raise BadRequest(e.key, **e.kwargs)
    manager.save_to_file()

    return schemas.AnimalResult(
        id=removed_animal.id,
        animal_type=removed_animal.animal_type,
        name=removed_animal.name
    )

@app.patch(
    "/animals/{id}",
    response_model=schemas.AnimalDetail,
    summary="動物の属性変更",
    description="動物の属性(種類・名前・特技)を変更します"
)
def edit_animal(id: int, req: schemas.AnimalEdit) -> schemas.AnimalDetail:
    update_data = req.model_dump(exclude_unset=True)
    
    try:
        target_animal = manager.get_animal(id)
        for attr, value in update_data.items():
            target_animal = manager.edit_animal(id, attr, value)
    except AnimalNotFoundError as e:
        raise NotFound(e.key, **e.kwargs)
    except ValidationError as e:
        raise BadRequest(e.key, **e.kwargs)

    manager.save_to_file()
    return schemas.AnimalDetail(
        id=target_animal.id,
        animal_type=target_animal.animal_type,
        name=target_animal.name,
        abilities=target_animal.get_all_ability()
    )

@app.get(
    "/animals/types",
    response_model=list[str],
    summary="動物の種類一覧取得",
    description="登録可能な動物の種類一覧を取得します")
def get_animal_types() -> list[str]:
    return manager.get_available_animal_types()

@app.get(
    "/animals/abilities",
    response_model=list[str],
    summary="特技一覧取得",
    description="登録可能な特技の一覧を取得します")
def get_abilities() -> list[str]:
    return manager.get_available_abilities()

@app.get(
    "/animals/{id}",
    response_model=schemas.AnimalDetail,
    summary="動物の詳細取得",
    description="指定したIDの動物の詳細情報を取得します"
)
def get_animal(id: int) -> schemas.AnimalDetail:
    try:
        animal = manager.get_animal(id)
    except AnimalNotFoundError as e:
        raise NotFound(e.key, **e.kwargs)

    return schemas.AnimalDetail(
        id=animal.id,
        animal_type=animal.animal_type,
        name=animal.name,
        abilities=animal.get_all_ability()
    )
    
@app.get(
    "/animals",
    response_model=list[schemas.AnimalDetail],
    summary="動物listの取得",
    description="検索条件(attr,keyword)を指定して、動物のリストを取得します"
)
def search_animal(
    search_attr: schemas.SearchAttr = schemas.SearchAttr.all, 
    keyword: str | None = None, 
    sort_by: schemas.SortAttr = schemas.SortAttr.id
    ) -> list[schemas.AnimalDetail]:
    """
    attr (Query Parameter): 検索対象の属性
    "すべて","ID", "種類", "名前", "特技" が指定可能
    keyword (Query Parameter): 検索したいキーワード (任意)
    """
    try:
        animals = manager.get_all_animals()
        if keyword:
            animals = manager.search_animal(search_attr.value, keyword)
        if sort_by:
            animals = manager.sort_list(animals, sort_by.name)
    except ValidationError as e:
        raise BadRequest(e.key, **e.kwargs)

    return [
        schemas.AnimalDetail(
            id=animal.id,
            animal_type=animal.animal_type,
            name=animal.name,
            abilities=animal.get_all_ability()
        ) for animal in animals
    ]

@app.get(
    "/animals/act/{ability}",
    response_model=list[schemas.ActionResult],
    summary="動物の特技実行",
    description="list内の動物に、指定した特技を実行させます"
)
def act_animal(ability: str) -> list[schemas.ActionResult]:
    try:
        result = manager.act_animal(ability)
    except ValidationError as e:
        raise BadRequest(e.key, **e.kwargs)
    return [
        schemas.ActionResult(
            name=item['animal'].name,
            animal_type=item['animal'].animal_type,
            action_key=item['action_key']
        ) for item in result
    ]

@app.post(
    "/system/clear",
    summary="データリセット",
    description="全てのデータを消去し初期状態に戻します")
def clear_data() -> dict[str, str]:
    manager.clear_data()
    manager.save_to_file()
    return {"message": "Data has been reset successfully"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)