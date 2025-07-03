#ブラウザから音声取得版。保留中
import streamlit as st
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase
import av
import numpy as np
import tempfile
import wave
import subprocess
import os
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase, WebRtcMode

class AudioRecorder(AudioProcessorBase):
    def __init__(self):
        self.frames = []
    def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
        pcm = frame.to_ndarray()
        if pcm.ndim == 2:
            pcm = np.mean(pcm, axis=0).astype(np.int16)  # モノラル変換
        elif pcm.ndim == 1:
            pcm = pcm.astype(np.int16)
        self.frames.append(pcm)
        return frame

st.title("🎙️ クライアント録音 × Whisper文字起こし")

# ユーザーが録音を開始
ctx = webrtc_streamer(
    key="audio",
    mode=WebRtcMode.SENDONLY,  # ← 修正ポイント！
    audio_processor_factory=lambda:AudioRecorder(),
    media_stream_constraints={"audio": True, "video": False},
)

# 録音されたデータを受け取る
if ctx.audio_processor and len(ctx.audio_processor.frames) > 0:
    st.write(f"🎧 録音フレーム数: {len(ctx.audio_processor.frames)}")
    if len(ctx.audio_processor.frames) > 0:
        st.write(f"🎧 最初のフレーム shape: {ctx.audio_processor.frames[0].shape}")

    if st.button("録音を文字起こし"):
        st.info("録音を保存して文字起こし中...")
        audio = np.concatenate(ctx.audio_processor.frames, axis=0)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
            with wave.open(f.name, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(48000)
                wf.writeframes(audio.tobytes())
            tmp_path = f.name
            # whisper-cli で文字起こし
        try:
            result = subprocess.run(
                [
                    "whisper.cpp/bin/whisper-cli",
                    "-m", "whisper.cpp/models/ggml-large-v3.bin",
                    "-f", tmp_path,
                    "-l", "ja",
                    "--no-timestamps"
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            st.success("文字起こし完了")
            st.text_area("文字起こし結果", result.stdout, height=300)
        except Exception as e:
            st.error(f"エラー: {e}")
        finally:
            os.remove(tmp_path)

#起動コマンド
#streamlit run transcribe_app.py --server.enableCORS false --server.enableXsrfProtection false --server.headless true --server.address 0.0.0.0 --server.port 8503 --server.sslCertFile cert.pem --server.sslKeyFile key.pem
