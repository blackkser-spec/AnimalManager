import uvicorn

if __name__ == "__main__":
    # APIパッケージ内のAPI_mainモジュールにあるappを起動
    uvicorn.run("API.api_main:app", host="0.0.0.0", port=8080, reload=True)