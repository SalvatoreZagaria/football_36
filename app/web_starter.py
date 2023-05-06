from app import factory


def create_app():
    return factory.create_app('api')


if __name__ == "__main__":
    app = create_app()
    app.run(port=int(8080))
