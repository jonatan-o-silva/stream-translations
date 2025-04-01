import streamlit as st
from streamlit_webrtc import WebRtcMode, webrtc_streamer
import queue
import time
from moviepy import VideoFileClip
from pathlib import Path
import openai
import pydub

PASTA_TEMP = Path(__file__).parent / 'temp'
PASTA_TEMP.mkdir(exist_ok=True)
ARQUIVO_AUDIO_TEMP = PASTA_TEMP / 'audio.mp3'
ARQUIVO_VIDEO_TEMP = PASTA_TEMP / 'video.mp4'
ARQUIVO_MIC_TEMP = PASTA_TEMP / 'mic.mp3'
print(ARQUIVO_AUDIO_TEMP)
client = openai.OpenAI()

if not 'transcricao_mic' in st.session_state:
    st.session_state['transcricao_mic'] = ''

def transcreve_tab_mic():
    prompt_input = st.text_input('(Opcional) Digite seu prompt', key='input_mic')
    webrtc_ctx = webrtc_streamer(
        key = 'recebe_audio',
        mode = WebRtcMode.SENDONLY,
        audio_receiver_size = 1024,
        media_stream_constraints={'video' : False, 'audio' : True}
    )

    if not webrtc_ctx.state.playing:
        st.write(st.session_state['transcricao_mic'])
        return
    container = st.empty()
    container.markdown('Comece a falar...')
    chunck_audio = pydub.AudioSegment.empty()
    tempo_ultima_descricao = time.time()

    while True:
        if webrtc_ctx.audio_receiver:
            try:
                frames_de_audio = webrtc_ctx.audio_receiver.get_frames(timeout=1)
            except queue.Empty:
                time.sleep(0.1)
                continue
            for frame in frames_de_audio:
                sound = pydub.AudioSegment(
                    data = frame.to_ndarray().tobytes(),
                    sample_width = frame.format.bytes,
                    frame_rate = frame.sample_rate,
                    channels = len(frame.layout.channels)
                )
                chunck_audio += sound

            agora = time.time()
            if len(chunck_audio) > 0 and agora - tempo_ultima_descricao > 5:
                tempo_ultima_descricao = agora
                chunck_audio.export(ARQUIVO_MIC_TEMP)
                with open(ARQUIVO_MIC_TEMP, 'rb') as arquivo_audio:
                    transcricao = client.audio.transcriptions.create(
                        model = 'whisper-1',
                        language = 'pt',
                        response_format = 'text',
                        file = arquivo_audio,
                        prompt=prompt_input
                    )
                    container.write(transcricao)
                    st.session_state['transcricao_mic'] = transcricao
        else:
            break


def transcreve_tab_video():
    prompt_input = st.text_input('(Opcional) Digite seu prompt', key='input_video')
    arquivo_video = st.file_uploader('Adicione um arquivo de video .mp4', type = ['mp4'])
    if not arquivo_video is None:
        with open(ARQUIVO_VIDEO_TEMP, mode='wb') as video_f:
            video_f.write(arquivo_video.read())
        moviepy_video = VideoFileClip(str(ARQUIVO_VIDEO_TEMP))
        moviepy_video.audio.write_audiofile(str(ARQUIVO_AUDIO_TEMP))
        with open(ARQUIVO_AUDIO_TEMP, 'rb') as arquivo_audio:
            transcricao = client.audio.transcriptions.create(
                model = 'whisper-1',
                language = 'pt',
                response_format = 'text',
                file = arquivo_audio,
                prompt=prompt_input
            )
            st.write(transcricao)

def transcreve_tab_audio():
    prompt_input = st.text_input('(Opcional) Digite seu prompt', key='input_audio')
    arquivo_audio = st.file_uploader('Adicione um arquivo de áudio .mp3', type = ['mp3'])
    if not arquivo_audio is None:
        transcricao = client.audio.transcriptions.create(
            model = 'whisper-1',
            language = 'pt',
            response_format = 'text',
            file = arquivo_audio,
            prompt=prompt_input
        )
        st.write(transcricao)

def main():
    st.header('Bem vindo ao Asimov Transcripts 🎤 ', divider=True)
    st. markdown('#### Transcreva áudio do microfone, de videos e de arquivos de áudio')
    tab_mic, tab_video, tab_audio = st.tabs(['Microfone', 'Video', 'Áudio'])
    with tab_mic:
        transcreve_tab_mic()
    with tab_video:
        transcreve_tab_video()
    with tab_audio:
        transcreve_tab_audio()



if __name__=='__main__':
    main()
