import sys, os, re, subprocess
import numpy as np, soundfile as sf
model = sys.argv[1]
TEXT = open("fetch/tts/uz/test.txt", encoding="utf-8").read().strip().replace("’","'").replace("ʻ","'").replace("`","'")
OUT = f"uzout/uz_test_{model}.wav"
os.makedirs("uzout", exist_ok=True)
REF = "uzout/ref.wav"
REF_TEXT = "Ronaldo ming golga yetishiga atigi o'n to'rtta gol qoldi! Messi esa undan qirq to'qqizta gol orqada."
def sentences(t):
    return [s for s in re.split(r'(?<=[.?!])\s+', t) if s.strip()]

def lat2cyr(t):
    rep = [("O'","Ў"),("o'","ў"),("G'","Ғ"),("g'","ғ"),("Sh","Ш"),("sh","ш"),("Ch","Ч"),("ch","ч"),
           ("Yo","Ё"),("yo","ё"),("Yu","Ю"),("yu","ю"),("Ya","Я"),("ya","я"),("Ye","Е"),("ye","е")]
    for a,b in rep: t = t.replace(a,b)
    t = re.sub(r"\b[Ee]", lambda m: "Э" if m.group(0)=="E" else "э", t)
    m = dict(zip("abdefghijklmnopqrstuvxyzABDEFGHIJKLMNOPQRSTUVXYZ","абдефгҳижклмнопқрстувхйзАБДЕФГҲИЖКЛМНОПҚРСТУВХЙЗ"))
    t = "".join(m.get(c,c) for c in t)
    return t.replace("'","ъ")

if model == "mms":
    import torch
    from transformers import VitsModel, AutoTokenizer
    mid = "facebook/mms-tts-uzb-script_cyrillic"
    tok = AutoTokenizer.from_pretrained(mid); m = VitsModel.from_pretrained(mid).eval()
    chunks = []
    torch.manual_seed(1)
    for s in sentences(TEXT):
        c = lat2cyr(s); print(c, flush=True)
        with torch.no_grad():
            w = m(**tok(c, return_tensors="pt")).waveform[0].numpy()
        chunks += [w, np.zeros(int(m.config.sampling_rate*0.25), dtype=np.float32)]
    sf.write(OUT, np.concatenate(chunks), m.config.sampling_rate)

elif model == "f5":
    from huggingface_hub import hf_hub_download
    from f5_tts.api import F5TTS
    ck = hf_hub_download("mrmuminov/f5-tts-uzbek", "model.safetensors")
    vo = hf_hub_download("mrmuminov/f5-tts-uzbek", "vocab.txt")
    tts = F5TTS(model="F5TTS_v1_Base", ckpt_file=ck, vocab_file=vo, device="cpu")
    tts.infer(ref_file=REF, ref_text=REF_TEXT, gen_text=TEXT, nfe_step=16, file_wave=OUT, seed=7)

elif model == "chatterbox":
    sys.path.insert(0, os.path.abspath("cbft")); os.chdir("cbft")
    import torch, inference as inf
    eng = inf.load_finetuned_engine_lora("cpu")
    inf.set_seed(42)
    chunks = []; sr = 24000
    for s in sentences(TEXT):
        print(s, flush=True)
        sr, a = inf.generate_sentence_audio(eng, s, "../"+REF, temperature=0.8, exaggeration=0.5, cfg_weight=0.5, repetition_penalty=2.0)
        if len(a): chunks += [a, np.zeros(int(sr*0.2), dtype=np.float32)]
    os.chdir("..")
    sf.write(OUT, np.concatenate(chunks), sr)
print("OK", OUT)
