from flask import Flask, render_template, request
import requests
import os

app = Flask(__name__)

# API BASE
API_BASE_URL = "https://taylor-swift-api.sarbo.workers.dev"

@app.route('/')
def index():
    """Página inicial"""
    return render_template('index.html')

@app.route('/albums')
def albums():
    """Lista todos os álbuns"""
    try:
        print("Tentando buscar álbuns...")
        response = requests.get(f"{API_BASE_URL}/albums", timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            albums_data = response.json()
            print(f"Encontrados {len(albums_data)} álbuns")
            
            if albums_data:
                print("Estrutura do primeiro álbum:", albums_data[0])
            
            return render_template('albums.html', albums=albums_data)
        else:
            return render_template('error.html', error="Não foi possível carregar os álbuns")
            
    except Exception as e:
        print(f"Erro em /albums: {e}")
        return render_template('error.html', error=str(e))

@app.route('/album/<path:album_id>')
def album_detail(album_id):
    # detalhes de algum album com ID
    try:
        print(f"Buscando álbum com ID: {album_id}")
        
        # Busca todos os álbuns
        albums_response = requests.get(f"{API_BASE_URL}/albums", timeout=10)
        albums_data = albums_response.json()
        
        # Busca todas as músicas
        songs_response = requests.get(f"{API_BASE_URL}/songs", timeout=10)
        all_songs = songs_response.json()
        
        album = None
       
        for a in albums_data:
            id_fields = ['id', '_id', 'albumId', 'album_id', 'number', 'index']
            
            for field in id_fields:
                if field in a and str(a[field]) == str(album_id):
                    album = a
                    print(f"Álbum encontrado pelo campo '{field}': {album.get('title', album.get('name', 'Sem título'))}")
                    break
            
            # quando encontrar o loop acaba
            if album:
                break
        
        if not album:
            for a in albums_data:
                title = a.get('title', a.get('name', '')).lower()
                if str(album_id).lower() in title or title in str(album_id).lower():
                    album = a
                    print(f"Álbum encontrado pelo título: {title}")
                    break
        
        if not album:
            print(f"Álbum com ID {album_id} não encontrado")
            return render_template('error.html', error=f"Álbum não encontrado (ID: {album_id})")
        
        # nome do album para achar as musicas dele
        album_name = album.get('title') or album.get('name') or ''
        album_name_lower = album_name.lower()
        
        # Filtra as músicas do álbum
        album_songs = []
        for song in all_songs:
            song_album = song.get('album') or song.get('albumName') or ''
            
            if album_name_lower and album_name_lower in song_album.lower():
                album_songs.append(song)
                continue
            
            song_album_id = str(song.get('albumId') or song.get('album_id') or '')
            if song_album_id and song_album_id == str(album_id):
                album_songs.append(song)
                continue
        
        print(f"Encontradas {len(album_songs)} músicas para o álbum '{album_name}'")
        
        return render_template('album_detail.html', album=album, songs=album_songs)
        
    except Exception as e:
        print(f"Erro em /album_detail: {e}")
        import traceback
        traceback.print_exc()
        return render_template('error.html', error=str(e))
    
@app.route('/songs')
def songs():
    try:
        print("Buscando músicas...")
        
        # busca músicas E álbuns para ter informações completas
        songs_response = requests.get(f"{API_BASE_URL}/songs", timeout=10)
        albums_response = requests.get(f"{API_BASE_URL}/albums", timeout=10)
        
        if songs_response.status_code == 200:
            songs_data = songs_response.json()
            albums_data = albums_response.json() if albums_response.status_code == 200 else []
            
            albums_dict = {}
            for album in albums_data:
                album_id = album.get('id') or album.get('_id')
                album_name = album.get('name') or album.get('title')
                if album_id and album_name:
                    albums_dict[album_id] = album_name
            
            print(f"Encontrados {len(albums_dict)} álbuns no dicionário")
            enriched_songs = []
            for song in songs_data:
                song_album = song.get('album') or 'Álbum desconhecido'
                
                # achar album pelo ID 
                album_id = song.get('albumId')
                if album_id and album_id in albums_dict:
                    song_album = albums_dict[album_id]
                
                # Cria uma cópia da música com informações melhoradas
                enriched_song = dict(song)
                enriched_song['album_display'] = song_album
                enriched_songs.append(enriched_song)
            
            # se houver parâmetro de busca, filtra pelo título
            query = request.args.get('q', '').strip().lower()
            if query:
                filtered = []
                for song in enriched_songs:
                    title = (song.get('name') or song.get('title') or '').lower()
                    if query in title:
                        filtered.append(song)
                print(f"Pesquisa '{query}' retornou {len(filtered)} músicas")
                enriched_songs = filtered
            else:
                print(f"Músicas processadas: {len(enriched_songs)}")

            return render_template('songs.html', songs=enriched_songs)
        else:
            return render_template('error.html', error="Não foi possível carregar as músicas")
            
    except Exception as e:
        print(f"Erro em /songs: {e}")
        return render_template('error.html', error=str(e))

@app.route('/quotes')
def quotes():
    """Lista todas as frases"""
    try:
        print("Buscando quotes...")
        response = requests.get(f"{API_BASE_URL}/quotes", timeout=10)
        
        if response.status_code == 200:
            quotes_data = response.json()
            print(f"Encontradas {len(quotes_data)} frases")
            return render_template('quotes.html', quotes=quotes_data)
        else:
            # Quotes de fallback
            fallback_quotes = [
                {"quote": "Long live the walls we crashed through", "song": "Long Live"},
                {"quote": "And you call me up again just to break me like a promise", "song": "All Too Well"},
                {"quote": "Band-Aids don't fix bullet holes", "song": "Bad Blood"},
                {"quote": "Darling, I'm a nightmare dressed like a daydream", "song": "Blank Space"},
                {"quote": "We are alone, just you and me", "song": "Sweet Nothing"},
                {"quote": "I don't wanna touch you, I don't wanna be just another ex-love you don't wanna see", "song": "End Game"},
                {"quote": "I could build a castle out of all the bricks they threw at me", "song": "New Romantics"},
                {"quote": "And if you never bleed, you're never gonna grow", "song": "The 1"},
                {"quote": "I’m so sick of running as fast as I can, wondering if I'd get there quicker if I was a man", "song": "The Man"},
                {"quote": "Don't you worry your pretty little mind, people throw rocks at things that shine", "song": "Ours"},
                {"quote": "Love you to the Moon and to Saturn", "song": "Seven"},
                {"quote": "Isn't it just so pretty to think all along there was some invisible string tying you to me?", "song": "Invisible String"},
                {"quote": "You are the best thing that's ever been mine", "song": "Mine"},
                {"quote": "All these people think love's for show, but I would die for you in secret", "song": "Peace"},
                {"quote": "I think I've seen this film before, and I didn't like the ending", "song": "Exile"},
                {"quote": "Everything you lose is a step you take", "song": "You're On Your Own, Kid"},
                {"quote": "A friend to all is a friend to none", "song": "Cardigan"},
                {"quote": "It's me, hi, I'm the problem, it's me", "song": "Anti-Hero"}
               
            ]
            return render_template('quotes.html', quotes=fallback_quotes)
            
    except Exception as e:
        print(f"Erro em /quotes: {e}")
        return render_template('error.html', error=str(e))

@app.route('/quiz')
def quiz():
    try:
        # Lista fixa de quotes para não depender da API
        quotes_list = [
            {"quote": "Long live the walls we crashed through", "song": "Long Live"},
            {"quote": "And you call me up again just to break me like a promise", "song": "All Too Well"},
            {"quote": "Darling, I'm a nightmare dressed like a daydream", "song": "Blank Space"},
            {"quote": "We are alone, just you and me", "song": "Sweet Nothing"},
            {"quote": "It's me, hi, I'm the problem, it's me", "song": "Anti-Hero"},
            {"quote": "Band-Aids don't fix bullet holes", "song": "Bad Blood"},
            {"quote": "I don't wanna touch you, I don't wanna be just another ex-love you don't wanna see", "song": "End Game"},
            {"quote": "I could build a castle out of all the bricks they threw at me", "song": "New Romantics"},
            {"quote": "And if you never bleed, you're never gonna grow", "song": "the 1"},
            {"quote": "Don't you worry your pretty little mind, people throw rocks at things that shine", "song": "Ours"},
            {"quote": "Love you to the Moon and to Saturn", "song": "seven"},
            {"quote": "You are the best thing that's ever been mine", "song": "Mine"},
            {"quote": "I think I've seen this film before, and I didn't like the ending", "song": "exile"},
            {"quote": "Everything you lose is a step you take", "song": "You're On Your Own, Kid"},
            {"quote": "A friend to all is a friend to none", "song": "cardigan"}
        ]
        
        import random
        
        # Pega uma frase aleatória
        current_quote = random.choice(quotes_list)
        correct_song = current_quote['song']
        
        # Lista de todas as músicas disponíveis
        all_songs = list(set([q['song'] for q in quotes_list]))
        
        # Remove a música correta da lista de opções
        other_songs = [s for s in all_songs if s != correct_song]
        
        # Pega 3 opções aleatórias
        options = random.sample(other_songs, 3)
        
        # Adiciona a correta e embaralha
        options.append(correct_song)
        random.shuffle(options)
        
        return render_template('quiz.html', 
                             quote=current_quote, 
                             options=options,
                             correct_song=correct_song)
        
    except Exception as e:
        print(f"Erro no quiz: {e}")
        return render_template('error.html', error="Não foi possível carregar o quiz")

@app.route('/check_answer', methods=['POST'])
def check_answer():
    """Verifica a resposta do quiz (versão simplificada)"""
    try:
        # Pega as respostas do formulário
        selected = request.form.get('selected')
        correct = request.form.get('correct')
        
        # Verifica se acertou
        is_correct = (selected == correct)
        
        # Lista fixa de quotes
        quotes_list = [
            {"quote": "Long live the walls we crashed through", "song": "Long Live"},
            {"quote": "And you call me up again just to break me like a promise", "song": "All Too Well"},
            {"quote": "Darling, I'm a nightmare dressed like a daydream", "song": "Blank Space"},
            {"quote": "We are alone, just you and me", "song": "Sweet Nothing"},
            {"quote": "It's me, hi, I'm the problem, it's me", "song": "Anti-Hero"},
            {"quote": "Band-Aids don't fix bullet holes", "song": "Bad Blood"},
            {"quote": "I don't wanna touch you, I don't wanna be just another ex-love you don't wanna see", "song": "End Game"},
            {"quote": "I could build a castle out of all the bricks they threw at me", "song": "New Romantics"},
            {"quote": "And if you never bleed, you're never gonna grow", "song": "the 1"},
            {"quote": "Don't you worry your pretty little mind, people throw rocks at things that shine", "song": "Ours"},
            {"quote": "Love you to the Moon and to Saturn", "song": "seven"},
            {"quote": "You are the best thing that's ever been mine", "song": "Mine"},
            {"quote": "I think I've seen this film before, and I didn't like the ending", "song": "exile"},
            {"quote": "Everything you lose is a step you take", "song": "You're On Your Own, Kid"},
            {"quote": "A friend to all is a friend to none", "song": "cardigan"}
        ]
        
        import random
        
        # Pega uma nova frase
        next_quote = random.choice(quotes_list)
        next_correct = next_quote['song']
        
        # Prepara novas opções
        all_songs = list(set([q['song'] for q in quotes_list]))
        other_songs = [s for s in all_songs if s != next_correct]
        options = random.sample(other_songs, 3)
        options.append(next_correct)
        random.shuffle(options)
        
        return render_template('quiz_result.html', 
                             is_correct=is_correct,
                             selected=selected,
                             correct=correct,
                             quote=next_quote,
                             options=options,
                             correct_song=next_correct)
        
    except Exception as e:
        print(f"Erro ao verificar resposta: {e}")
        return render_template('error.html', error=f"Erro ao processar resposta: {str(e)}")

# ERRO 404
@app.errorhandler(404)
def page_not_founded(error):
    return render_template('erro404.html'), 404

# ERRO 500 - Erros internos do servidor
@app.errorhandler(500)
def erro_interno(error):
    return render_template('erro500.html'), 500

if __name__ == '__main__':
    app.run(debug=True)