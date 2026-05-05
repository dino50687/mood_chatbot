if __name__ == "__main__":
    import app
    print("Te:", app.get_llm_response("hi", "happy", "te"))
    print("Hi:", app.get_llm_response("hi", "happy", "hi"))
    print("En:", app.get_llm_response("hi", "happy", "en"))
