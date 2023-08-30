from flask import Flask, render_template, request
import asyncio
import pokedex

app = Flask(__name__)


#Em resumo, o objetivo desse código é fornecer uma maneira de executar uma corrotina assíncrona de forma síncrona, encapsulando a chamada asyncio.run() dentro da função func. Isso pode ser útil em situações onde você deseja executar uma corrotina assíncrona em um contexto que espera uma função síncrona. No entanto, para usar esse código, você precisaria ter o módulo asyncio importado, pois ele é usado para criar o loop assíncrono.
def async_wrapper(coro):
    def func(*args, **kwargs):
        return asyncio.run(coro(*args, **kwargs))
    return func


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'search-button' in request.form:
            search_term = request.form.get('search_term', '')  # Obtenha o termo de pesquisa do formulário
            if search_term:  # Realize a pesquisa aqui usando o search_term
                if search_term:
                    resultados, quantidade, offset, desativarButtonPrev, desativarButtonNext = async_wrapper(
                        pokedex.pesquisar_pokemon_por_nome)(search_term)
                    return render_template('index.html', resultados_pesquisa=resultados, total_pokemon_count=quantidade, offset=quantidade,desativarButtonPrev=desativarButtonPrev, desativarButtonNext=desativarButtonNext)
            else:
                nomes_tipos_sprites, total_pokemon_count, offset, desativarButtonPrev = async_wrapper(
                    pokedex.pokedexWLimit)()
                offset += 36
                if offset > total_pokemon_count:
                    offset = total_pokemon_count
                return render_template('index.html', nomes_tipos_sprites=nomes_tipos_sprites,
                                       total_pokemon_count=total_pokemon_count, offset=offset,
                                       desativarButtonPrev=desativarButtonPrev)

        if 'next-button' in request.form:
            # Ação a ser realizada quando o botão "Next" for pressionado
            nomes_tipos_sprites, total_pokemon_count, offset, desativarButtonNext = async_wrapper(pokedex.nextpage)()
            offset += 36
            if offset > total_pokemon_count:
                offset = total_pokemon_count
            return render_template('index.html', nomes_tipos_sprites=nomes_tipos_sprites, total_pokemon_count=total_pokemon_count,offset=offset,desativarButtonNext=desativarButtonNext)
        elif 'prev-button' in request.form:
            # Ação a ser realizada quando o botão "Prev" for pressionado
            nomes_tipos_sprites, total_pokemon_count, offset, desativarButtonPrev = async_wrapper(pokedex.prevpage)()
            offset += 36
            if offset > total_pokemon_count:
                offset = total_pokemon_count
            return render_template('index.html', nomes_tipos_sprites=nomes_tipos_sprites, total_pokemon_count=total_pokemon_count,offset=offset,desativarButtonPrev=desativarButtonPrev)

    else:
        nomes_tipos_sprites, total_pokemon_count, offset, desativarButtonPrev = async_wrapper(pokedex.pokedexWLimit)()
        offset += 36
        if offset > total_pokemon_count:
            offset = total_pokemon_count
        return render_template('index.html', nomes_tipos_sprites=nomes_tipos_sprites, total_pokemon_count=total_pokemon_count,offset=offset, desativarButtonPrev=desativarButtonPrev)
        pass


@app.route('/pokemon/<int:pokemon_id>', methods=['GET'])
def pokemon_details(pokemon_id):

    pokemon_infos, abilities_and_effects = async_wrapper(pokedex.solo_pokemon_info)(pokemon_id)

    return render_template('pokemon_info.html', pokemon=pokemon_infos, abilities_and_effects=abilities_and_effects)


if __name__ == '__main__':
    app.run(debug=True)  # Run app