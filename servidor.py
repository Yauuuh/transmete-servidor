import asyncio
import websockets
import json
import random
import os

salas = {}

async def carteiro(websocket):
    try:
        async for mensagem in websocket:
            dados = json.loads(mensagem)
            acao = dados.get("acao")

            if acao == "criar_sala":
                codigo = str(random.randint(1000, 9999))
                salas[codigo] = {"anfitriao": websocket, "espectadores": {}}
                await websocket.send(json.dumps({"acao": "sala_criada", "codigo": codigo}))
                print(f"🏠 Sala {codigo} criada!")

            elif acao == "entrar_sala":
                codigo = dados.get("codigo")
                if codigo in salas:
                    id_espectador = str(id(websocket)) 
                    salas[codigo]["espectadores"][id_espectador] = websocket
                    print(f"👤 Novo espectador na sala {codigo}")
                    await salas[codigo]["anfitriao"].send(json.dumps({
                        "acao": "novo_espectador",
                        "id_espectador": id_espectador
                    }))
                else:
                    await websocket.send(json.dumps({"acao": "erro", "mensagem": "Sala não encontrada"}))

            elif acao == "oferta":
                codigo = dados.get("codigo")
                id_espectador = dados.get("id_espectador")
                if codigo in salas and id_espectador in salas[codigo]["espectadores"]:
                    espectador_ws = salas[codigo]["espectadores"][id_espectador]
                    await espectador_ws.send(json.dumps({
                        "acao": "oferta",
                        "sdp": dados["sdp"],
                        "tipo": dados["tipo"]
                    }))

            elif acao == "resposta":
                codigo = dados.get("codigo")
                if codigo in salas:
                    anfitriao_ws = salas[codigo]["anfitriao"]
                    await anfitriao_ws.send(json.dumps({
                        "acao": "resposta",
                        "id_espectador": str(id(websocket)),
                        "sdp": dados["sdp"],
                        "tipo": dados["tipo"]
                    }))
    except websockets.exceptions.ConnectionClosed:
        print("🔌 Alguém desconectou da rede.")

async def main():
    # Pega a porta automática da nuvem (ou usa 8765 se rodar local)
    porta = int(os.environ.get("PORT", 8765))
    # 0.0.0.0 significa "Aberto para a internet"
    async with websockets.serve(carteiro, "0.0.0.0", porta):
        print(f"📮 Servidor de Sinalização rodando na porta {porta}!")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())