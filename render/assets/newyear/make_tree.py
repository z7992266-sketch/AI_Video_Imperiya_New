# Animated New Year tree corner sticker (original drawing), transparent, loops seamlessly.
import math, random, os
from PIL import Image, ImageDraw, ImageFilter
S=2; W,H=240,320; FPS=30; N=120  # 4 s loop
out='frames'; os.makedirs(out,exist_ok=True)
random.seed(7)
cx=W//2
tiers=[(78,100,215),(62,82,160),(46,62,108)]  # (top y offset not used)
# tree layers: (apex_y, base_y, half_width)
layers=[(70,175,62),(110,225,82),(150,275,102)]
lights=[]
for (ay,by,hw) in layers:
    for k in range(7):
        t=random.uniform(0.25,0.95); y=ay+(by-ay)*t; x=cx+random.uniform(-1,1)*hw*t*0.85
        lights.append((x,y,random.choice([(255,70,70),(255,210,60),(80,200,255),(120,255,140),(255,120,220)]),random.uniform(0,2*math.pi)))
balls=[(cx-40,205,(220,40,50)),(cx+38,190,(240,190,40)),(cx-12,250,(60,130,240)),(cx+55,255,(220,40,50)),(cx+5,150,(240,190,40)),(cx-58,262,(240,190,40))]
snow=[(random.uniform(0,W),random.uniform(0,H),random.uniform(1.2,2.6),random.uniform(0,2*math.pi)) for _ in range(26)]
def star(d,x,y,r,col):
    pts=[]
    for i in range(10):
        a=-math.pi/2+i*math.pi/5; rr=r if i%2==0 else r*0.45
        pts.append((x+rr*math.cos(a),y+rr*math.sin(a)))
    d.polygon([(px*S,py*S) for px,py in pts],fill=col)
for f in range(N):
    ph=2*math.pi*f/N
    im=Image.new('RGBA',(W*S,H*S),(0,0,0,0)); d=ImageDraw.Draw(im)
    sway=math.sin(ph)*2.0
    # soft shadow/glow base
    glow=Image.new('RGBA',im.size,(0,0,0,0)); g=ImageDraw.Draw(glow)
    g.ellipse([(cx-95)*S,(282)*S,(cx+95)*S,(304)*S],fill=(0,0,0,110))
    im=Image.alpha_composite(im,glow.filter(ImageFilter.GaussianBlur(8*S))); d=ImageDraw.Draw(im)
    # trunk
    d.rounded_rectangle([(cx-13)*S,272*S,(cx+13)*S,300*S],radius=4*S,fill=(110,70,40))
    # tree tiers (bottom first), with outline for readability on any background
    for (ay,by,hw) in reversed(layers):
        sx=sway*(1-(ay/300))
        poly=[(cx+sx,ay-6),(cx-hw,by),(cx+hw,by)]
        d.polygon([(x*S,y*S) for x,y in poly],fill=(20,110,55),outline=(255,255,255),width=3*S)
        d.polygon([(x*S,y*S) for x,y in [(cx+sx,ay+4),(cx-hw*0.55,by-6),(cx+sx,by-6)]],fill=(28,135,68))
    # garland
    for i,(ay,by,hw) in enumerate(layers):
        y0=ay+(by-ay)*0.6
        pts=[(cx-hw*0.6+j*hw*1.2/20, y0+ (j/20)*18 + math.sin(j/3+ph)*1.5) for j in range(21)]
        d.line([(x*S,y*S) for x,y in pts],fill=(255,215,90),width=2*S)
    for bx,by,c in balls:
        d.ellipse([(bx-8)*S,(by-8)*S,(bx+8)*S,(by+8)*S],fill=c,outline=(255,255,255),width=S)
        d.ellipse([(bx-4)*S,(by-5)*S,(bx-1)*S,(by-2)*S],fill=(255,255,255,200))
    # twinkling lights
    lay=Image.new('RGBA',im.size,(0,0,0,0)); l=ImageDraw.Draw(lay)
    for x,y,c,p in lights:
        a=0.5+0.5*math.sin(ph*2+p)
        r=3+2.5*a
        l.ellipse([(x-r*2)*S,(y-r*2)*S,(x+r*2)*S,(y+r*2)*S],fill=c+(int(110*a),))
    lay=lay.filter(ImageFilter.GaussianBlur(4*S)); im=Image.alpha_composite(im,lay); d=ImageDraw.Draw(im)
    for x,y,c,p in lights:
        a=0.5+0.5*math.sin(ph*2+p); r=2.2+1.2*a
        d.ellipse([(x-r)*S,(y-r)*S,(x+r)*S,(y+r)*S],fill=tuple(min(255,int(v*(0.6+0.4*a)+60*a)) for v in c))
    # star with pulse + glow
    sr=17+2.5*math.sin(ph*2)
    gl=Image.new('RGBA',im.size,(0,0,0,0)); star(ImageDraw.Draw(gl),cx+sway,58,sr+8,(255,220,80,150))
    im=Image.alpha_composite(im,gl.filter(ImageFilter.GaussianBlur(6*S))); d=ImageDraw.Draw(im)
    star(d,cx+sway,58,sr,(255,215,60)); 
    # snow (loops: fall exactly H over the loop)
    for x,y,r,p in snow:
        yy=(y+H*f/N)%H; xx=x+math.sin(ph+p)*6
        d.ellipse([(xx-r)*S,(yy-r)*S,(xx+r)*S,(yy+r)*S],fill=(255,255,255,230))
    im=im.resize((W,H),Image.LANCZOS)
    im.save(f'{out}/f{f:03d}.png')
print('ok')
