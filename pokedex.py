import requests
from bs4 import BeautifulSoup
# async imports
import aiohttp
import asyncio

from pprint import pprint

API_URL = 'https://pokeapi.co/api/v2/'
pokedexLimit = 36
# variável para calcular o offset de cada página
offset = 0
# variáveis para determinar quando desativar os botões de paginação(True = desativado)
desativarButtonPrev = False
desativarButtonNext = False
total_pokemon_count = 0
multiplo_mais_proximo = 0


# pesquisar para entender
async def fetch_url(session, url):
    async with session.get(url) as response:
        return await response.json()


# função async para o total de pokémons
async def get_total_pokemon_count():
    # O trecho de código async with aiohttp.ClientSession() as session: é usado para criar e gerenciar uma sessão HTTP assíncrona usando a biblioteca aiohttp
    async with aiohttp.ClientSession() as session:
        # busca a url do pokemon = response
        response = await fetch_url(session, API_URL + 'pokemon')
        # a contagem do total = total_count
        total_count = response['count']
        return total_count


# busca a url de cada pokémon de acordo com o id especificado no WLimit, Next e Prev
async def get_pokemons_sprites(pokemon_id):
    base_url = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/"
    return base_url + f"{pokemon_id}.png"


# pega o pokemon_url de cada um, dentro desse link obtém os tipos através do tipos[] = ...
async def obter_tipos_async(session, pokemon_url):
    detalhes_pokemon = await fetch_url(session, pokemon_url)
    tipos = [tipo['type']['name'] for tipo in detalhes_pokemon['types']]
    return tipos


async def solo_pokemon_info(pokemon_id):
    # 'link de busca' do pokémon com id selecionado
    link_poke_api = API_URL + "pokemon/"+str(pokemon_id)
    async with aiohttp.ClientSession() as session:
        requisicao_pokemon = await fetch_url(session, link_poke_api) # busca o url de cada 'link de busca' = requisicao_pokemon

        infos = [] # ARRAY GERAL

        # URL da página da Bulbapedia
        bulbapedia_url = f"https://bulbapedia.bulbagarden.net/wiki/Pok%C3%A9mon_category#{pokemon_id:03d}"

        # Fazendo a requisição à página da Bulbapedia
        response = requests.get(bulbapedia_url)
        soup = BeautifulSoup(response.content, "html.parser")

        # Encontrando a tabela com as informações de categoria
        category_table = soup.find("table", {"class": "sortable"})

        if category_table:
            # Encontre todas as linhas da tabela
            rows = category_table.find_all("tr")

            for row in rows:
                # Encontre as células da linha
                cells = row.find_all("td")

                # Verifique se a linha possui células suficientes (pode variar)
                if len(cells) >= 4:
                    # O quarto elemento é a "English Category"
                    english_category = cells[3].text.strip()

                    # Formate o ID do Pokémon para ter comprimento fixo de 4 caracteres com zeros à esquerda
                    cell_id = cells[0].text.strip().zfill(4)
                    if pokemon_id <= 1000: #Problema com pokémons mais novos
                        if cell_id == str(pokemon_id).zfill(4):
                            seed = english_category.replace(" Pokémon", "")  # Remove " Pokémon"
                            break  # Saia do loop, pois encontramos a categoria
                    else:
                        seed = 'Not found'
                        break  # Saia do loop, pois o pokémons é id = 1000 ou maior


        nome = requisicao_pokemon['name'] # NOME DO POKÉMON
        tipos_data = await obter_tipos_async(session, link_poke_api)
        sprite_url = await get_pokemons_sprites(pokemon_id)

        weight = requisicao_pokemon["weight"]
        height = requisicao_pokemon["height"]

        hp = requisicao_pokemon["stats"][0]["base_stat"]  # HP stat is at index 0 in the stats list
        attack = requisicao_pokemon["stats"][4]["base_stat"]  # Attack stat is at index 4 in the stats list
        defense = requisicao_pokemon["stats"][3]["base_stat"]  # Defense stat is at index 3 in the stats list
        special_attack = requisicao_pokemon["stats"][2]["base_stat"]  # Special Attack stat is at index 2 in the stats list
        special_defense = requisicao_pokemon["stats"][1]["base_stat"]  # Special Defense stat is at index 1 in the stats list
        speed = requisicao_pokemon["stats"][5]["base_stat"]  # Speed stat is at index 5 in the stats list
        abilities = [ability["ability"]["name"] for ability in requisicao_pokemon["abilities"]]

        abilitiesUrls = [abilityUrl["ability"]["url"] for abilityUrl in requisicao_pokemon["abilities"]]

        def get_effect(ability_url):
            response = requests.get(ability_url)
            data = response.json()

            effect_entries = data["effect_entries"]
            effect = None

            # checar todos os 'effect_entries' como linguagens diferentes, até achar uma em inglês
            for entry in effect_entries:
                if entry["language"]["name"] == "en":
                    effect = entry["effect"]

                    break

            return effect

        effect_data = []
        for url in abilitiesUrls:
            effect = get_effect(url)
            if effect:
                effect_data.append(effect)
            else:
                print("Effect not found")

        infos.append({
            'id': pokemon_id,
            'nome': nome,
            'tipos': tipos_data,
            'sprite_url': sprite_url,
            'seed': seed,
            'weight': weight/10,
            'height': height/10,
            'hp': hp,
            'attack': attack,
            'defense': defense,
            'special_attack': special_attack,
            'special_defense': special_defense,
            'speed': speed,
            'abilities': abilities,
            'effects': effect_data
        })
        pokemon_infos = infos[0]  #converter uma lista que contém um dicionário em um dicionário

        abilities_and_effects = []

        for ability, effect in zip(pokemon_infos['abilities'], pokemon_infos['effects']):
            abilities_and_effects.append({'ability': ability, 'effect': effect})

        print(abilities_and_effects)

        return pokemon_infos, abilities_and_effects


async def for_processos_armazenamento_array(session, requisicao_pokemon):
    # ===== ARRAYS =====
    nomes_tipos_sprites = []  # array GERAL(para o final (return))
    sprite_data = []  # arrays para guardar sprites até colocá-las no nomes_tipos_sprites[]
    tipos_data = []  # arrays para guardar tipos até colocá-las no nomes_tipos_sprites[]

    # for para chamar todas as informações necessárias (FOR DE PROCESSOS)
    for i, pokemon_info in enumerate(requisicao_pokemon['results']):
        # ===== SPRITES =====
        pokemon_id = i + offset + 1  # cálculo para armazenar em pokemon_id o id correto de cada pokemon sprite
        # armazena no 'sprite_url' cada requisição da função get_pokemons_sprites onde puxa os links dos sprites
        sprite_url = await get_pokemons_sprites(pokemon_id)
        sprite_data.append({  # armazena cada sprite dos pokémons no sprite_data
            'sprite_url': sprite_url
        })

        # ===== TIPOS =====
        # armazena cada tipo dos pokémons no tipos_data
        tipos_data.append(obter_tipos_async(session, pokemon_info['url']))

    tipos_list = await asyncio.gather(*tipos_data)  # executa a async dos tipos para a array tipos_list[]
    # recomeça o for (pausa para o tipos_list carregar corretamente)

    # (FOR FINAL) mesmo for de cima, porém agora para ARMAZENAR TODOS OS DADOS e dar o RETURN
    for i, pokemon_info in enumerate(requisicao_pokemon['results']):
        pokemon_id = int(pokemon_info['url'].split('/')[-2])
        nome = pokemon_info['name']  # Armazena os nomes dos pokemons na variável
        tipos = tipos_list[i]  # Pegar os tipos corretos usando o i e armazenar na variável
        sprite_url = sprite_data[i]['sprite_url']  # Pegar o sprite_url correto usando o i e armazenar na variável

        # passo final onde pega cada item presente nas variáveis e coloca-os na array 'nomes_tipos_sprites[]'
        nomes_tipos_sprites.append({
            'id': pokemon_id,
            'nome': nome,
            'tipos': tipos,
            'sprite_url': sprite_url
        })
    return nomes_tipos_sprites


# função chamada ao início do código
async def pokedexWLimit():
    global API_URL, pokedexLimit, total_pokemon_count, multiplo_mais_proximo, desativarButtonPrev, offset

    desativarButtonPrev = True

    # 'link de busca' aos pokémons em quantidade selecionada
    link_poke_api = API_URL + "pokemon?limit=" + str(pokedexLimit)
    # O trecho de código async with aiohttp.ClientSession() as session: é usado para criar e gerenciar uma sessão HTTP assíncrona usando a biblioteca aiohttp
    async with aiohttp.ClientSession() as session:
        # de forma assincrona, busca o url de cada 'link de busca' = requisicao_pokemon
        requisicao_pokemon = await fetch_url(session, link_poke_api)

        # executa a função do total de pokémons e do múltiplo mais próximo desse total
        total_pokemon_count = await get_total_pokemon_count()
        multiplo_mais_proximo = (total_pokemon_count // pokedexLimit) * pokedexLimit
        print("Total de Pokémons:", total_pokemon_count)

        # executa a função 'for' e armazena os dados em 'nomes_tipos_sprites[]'
        nomes_tipos_sprites = await for_processos_armazenamento_array(session, requisicao_pokemon)

        return nomes_tipos_sprites, total_pokemon_count, offset, desativarButtonPrev


async def nextpage():
    global offset, pokedexLimit, desativarButtonNext, total_pokemon_count, multiplo_mais_proximo

    if offset < multiplo_mais_proximo + 1:  # apenas para caso de bugs
        offset += pokedexLimit  # a cada clique no 'next', adiciona offsets = pokedexLimit

        # 'link de busca' aos pokémons em quantidade selecionada e offset correto
        link_poke_api = API_URL + "pokemon?limit=" + str(pokedexLimit) + "&offset=" + str(offset)
        print('next')
        print(offset)

        # O trecho de código async with aiohttp.ClientSession() as session: é usado para criar e gerenciar uma sessão HTTP assíncrona usando a biblioteca aiohttp
        async with aiohttp.ClientSession() as session:
            # de forma assincrona, busca o url de cada 'link de busca' = requisicao_pokemon
            requisicao_pokemon = await fetch_url(session, link_poke_api)

            i = 0
            if offset == multiplo_mais_proximo:
                # executa a função 'for' e armazena os dados em 'nomes_tipos_sprites[]'
                nomes_tipos_sprites = await for_processos_armazenamento_array(session, requisicao_pokemon)

            else:
                # executa a função 'for' e armazena os dados em 'nomes_tipos_sprites[]'
                nomes_tipos_sprites = await for_processos_armazenamento_array(session, requisicao_pokemon)

        # verifica se o offset é maior que o multiplo_mais_proximo para poder desativar o botão
        if offset >= multiplo_mais_proximo:
            desativarButtonNext = True
            return nomes_tipos_sprites, total_pokemon_count, offset, desativarButtonNext
        else:
            desativarButtonNext = False
            return nomes_tipos_sprites, total_pokemon_count, offset, desativarButtonNext
    else:  # em caso de bug e o usuário conseguir apertar o 'prev', executará o início do código
        desativarButtonPrev = True

        print('next bug')
        print(offset)
        nomes_tipos_sprites = await pokedexWLimit()

        return nomes_tipos_sprites, total_pokemon_count, offset, desativarButtonPrev


async def prevpage():
    global offset, pokedexLimit, desativarButtonPrev, total_pokemon_count

    if offset >= pokedexLimit:  # apenas para caso de bugs
        offset -= pokedexLimit  # a cada clique no 'prev', diminui offsets = pokedexLimit
        # 'link de busca' aos pokémons em quantidade selecionada e offset correto
        link_poke_api = API_URL + "pokemon?limit=" + str(pokedexLimit) + "&offset=" + str(offset)
        print('prev')
        print(offset)

        # O trecho de código async with aiohttp.ClientSession() as session: é usado para criar e gerenciar uma sessão HTTP assíncrona usando a biblioteca aiohttp
        async with aiohttp.ClientSession() as session:
            # de forma assincrona, busca o url de cada 'link de busca' = requisicao_pokemon
            requisicao_pokemon = await fetch_url(session, link_poke_api)

            # executa a função 'for' e armazena os dados em 'nomes_tipos_sprites[]'
            nomes_tipos_sprites = await for_processos_armazenamento_array(session, requisicao_pokemon)

            # verifica se o offset é menor que o pokedexLimit para poder desativar o botão
            if offset < pokedexLimit:
                desativarButtonPrev = True
                return nomes_tipos_sprites, total_pokemon_count, offset, desativarButtonPrev
            else:
                desativarButtonPrev = False
                return nomes_tipos_sprites, total_pokemon_count, offset, desativarButtonPrev
    else:  # em caso de bug e o usuário conseguir apertar o 'prev', executará o início do código
        desativarButtonPrev = True
        print('prev bug')
        print(offset)
        nomes_tipos_sprites = await pokedexWLimit()

        return nomes_tipos_sprites, total_pokemon_count, offset, desativarButtonPrev


async def pesquisar_pokemon_por_nome(nome_parcial):
    global desativarButtonPrev, desativarButtonNext

    async with aiohttp.ClientSession() as session:
        url = API_URL + 'pokemon?limit=1500'
        response = await fetch_url(session, url)
        resultados = []
        quantidade = 0
        limite = 48

        for pokemon_info in response['results']:
            if quantidade >= limite:
                break  # Sai do loop quando a quantidade atingir o limite máximo
            nome_pokemon = pokemon_info['name'] #GET_name
            if nome_parcial.lower() in nome_pokemon:
                if nome_parcial.lower() in nome_pokemon:
                    pokemon_id = int(pokemon_info['url'].split('/')[-2])
                    print(pokemon_id)

                    sprite_url = await get_pokemons_sprites(pokemon_id) #GET_sprite
                    tipos = await obter_tipos_async(session, pokemon_info['url']) #GET_tipos
                    dados_pokemon = {
                        'id': pokemon_id,
                        'nome': nome_pokemon,
                        'tipos': tipos,
                        'sprite_url': sprite_url
                    }
                    resultados.append(dados_pokemon)
                    quantidade += 1

        desativarButtonPrev = True
        desativarButtonNext = True
        return resultados, quantidade, quantidade, desativarButtonPrev, desativarButtonNext