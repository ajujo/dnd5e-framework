import requests

def probar_conexion():
    url = "http://localhost:1234/v1/chat/completions"

    payload = {
        "model": "local-model",
        "messages": [
            {"role": "user", "content": "Di solamente: conexión exitosa"}
        ],
        "max_tokens": 50,
        "temperature": 0.7
    }

    try:
        respuesta = requests.post(url, json=payload, timeout=30)
        respuesta.raise_for_status()

        datos = respuesta.json()
        texto = datos["choices"][0]["message"]["content"]

        print("✓ Conexión exitosa con LM Studio")
        print(f"Respuesta del LLM: {texto}")
        return True

    except requests.exceptions.ConnectionError:
        print("✗ Error: No se pudo conectar con LM Studio")
        print("  Verifica que el servidor esté iniciado")
        return False

    except Exception as e:
        print(f"✗ Error inesperado: {e}")
        return False

if __name__ == "__main__":
    probar_conexion()

