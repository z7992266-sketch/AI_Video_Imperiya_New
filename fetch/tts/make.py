import soundfile as sf, numpy as np, subprocess, os, urllib.request
os.makedirs('fetch/out/tts', exist_ok=True)
EN = ("Glitch Diary, entry number three. Today I found a lake in Antarctica that bleeds. "
      "Blood-red water pours out of a white glacier, and for almost a century nobody could explain why. "
      "But that's not the strangest part. The water underneath has been sealed off for over a million years, "
      "and something is still alive down there.")
from kokoro import KPipeline
p = KPipeline(lang_code='a')
for v in ['af_heart', 'af_bella', 'am_michael']:
    audio = np.concatenate([a for _, _, a in p(EN, voice=v, speed=0.95)])
    sf.write(f'fetch/out/tts/en_{v}.wav', audio, 24000)
RU = ("Почти девятьсот лет стоит этот минарет — и, говорят, его пощадил даже Чингисхан. "
      "Минарет Калян в Бухаре построили в тысяча сто двадцать седьмом году. "
      "Его фундамент такой глубокий, что археологи так и не дошли до его дна.")
base = 'https://huggingface.co/rhasspy/piper-voices/resolve/main/ru/ru_RU/'
for name, path in [('dmitri', 'dmitri/medium/ru_RU-dmitri-medium'), ('irina', 'irina/medium/ru_RU-irina-medium'), ('denis', 'denis/medium/ru_RU-denis-medium')]:
    for ext in ['.onnx', '.onnx.json']:
        urllib.request.urlretrieve(base + path + ext, f'/tmp/{name}{ext}')
    subprocess.run(['piper', '-m', f'/tmp/{name}.onnx', '-f', f'fetch/out/tts/ru_{name}.wav'], input=RU.encode(), check=True)
for f in os.listdir('fetch/out/tts'):
    if f.endswith('.wav'):
        w = 'fetch/out/tts/' + f
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', w, '-af', 'loudnorm=I=-16', '-b:a', '128k', w[:-4] + '.mp3'], check=True)
        os.remove(w)
