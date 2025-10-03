import json

psfile = open("pet.json", "r")
petshop = json.load(psfile)

tempo = 0
sl_interior = []
fila = []
timeline = []
pets = sorted(petshop["workload"]["animals"], key=lambda x: (x["arrival_time"], x["id"]))

while pets or fila or sl_interior:
    chegada = [i for i in pets if i["arrival_time"] == tempo]
    for i in chegada:
        fila.append(i)
    pets = [i for i in pets if i not in chegada]

    estado = bool(sl_interior)
    if sl_interior:
        sl_interior = [
            animal for animal in sl_interior
            if (animal.get("entry_time", 0) + animal["rest_duration"]) > tempo
        ]

    esvaziou = estado and not sl_interior
    
    if not sl_interior:
        estado_ant = "EMPTY"
    elif all(i["species"] == "DOG" for i in sl_interior):
        estado_ant = "DOGS"
    else:
        estado_ant = "CATS"

    if tempo > 0 and not esvaziou:
        if estado_ant == "EMPTY" and fila:
            especie_entrando = fila[0]["species"]
            entrando = [i for i in fila if i["species"] == especie_entrando]
            for i in entrando:
                i["entry_time"] = tempo
                sl_interior.append(i)
            fila = [i for i in fila if i not in entrando]
        elif estado_ant == "DOGS":
            entrando = [i for i in fila if i["species"] == "DOG"]
            for i in entrando:
                i["entry_time"] = tempo
                sl_interior.append(i)
            fila = [i for i in fila if i not in entrando]
        elif estado_ant == "CATS":
            entrando = [i for i in fila if i["species"] == "CAT"]
            for i in entrando:
                i["entry_time"] = tempo
                sl_interior.append(i)
            fila = [i for i in fila if i not in entrando]

    if not sl_interior:
        estado_final = "EMPTY"
    elif all(i["species"] == "DOG" for i in sl_interior):
        estado_final = "DOGS"
    else:
        estado_final = "CATS"

    detalhes_pet = []
    for i, animal in enumerate(sl_interior):
        tempo_saida = animal.get("entry_time", 0) + animal["rest_duration"]
        tempo_restante = tempo_saida - tempo
        
        if i > 0 and tempo_restante <= 0:
            status = "ok"
        else:
            status = str(tempo_restante)
            
        detalhes_pet.append(f"{animal['id']}({status})")
        
    timeline.append({
        "time": tempo,
        "room_state": estado_final,
        "inside": detalhes_pet,
        "waiting": [i["id"] for i in fila]
    })    
    tempo += 1
psfile.close()

for step in timeline:
    print(f"Tick={step['time']:02d} | ESTADO: {step['room_state']:6} | "
          f"SALA: {sorted(step['inside'])} | ESPERA: {sorted(step['waiting'])}")