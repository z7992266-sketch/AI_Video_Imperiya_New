from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
import random
random.seed(7)
F="/usr/share/fonts/opentype/inter/"
BLACK=F+"Inter-Black.otf"; MED=F+"Inter-Medium.otf"; MONO="/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
BG=(6,8,14); CY=(0,229,255); MG=(255,0,110); WH=(240,246,255)

def bg(w,h):
    im=Image.new("RGB",(w,h),BG)
    # radial glow
    g=Image.new("L",(w,h),0); d=ImageDraw.Draw(g)
    d.ellipse((w*0.2,h*-0.2,w*0.8,h*1.2),fill=90)
    g=g.filter(ImageFilter.GaussianBlur(min(w,h)//4))
    im=Image.composite(Image.new("RGB",(w,h),(20,40,70)),im,g)
    d=ImageDraw.Draw(im)
    step=max(24,w//60)
    for x in range(0,w,step): d.line((x,0,x,h),fill=(14,22,36),width=1)
    for y in range(0,h,step): d.line((0,y,w,y),fill=(14,22,36),width=1)
    # binary rain bits
    fm=ImageFont.truetype(MONO,max(12,step//2))
    for _ in range(w*h//9000):
        x=random.randrange(0,w,step); y=random.randrange(0,h,step)
        d.text((x+3,y+2),random.choice("01"),font=fm,fill=(20,60,80))
    # scanlines
    sl=Image.new("RGB",(w,h),(0,0,0)); sd=ImageDraw.Draw(sl)
    for y in range(0,h,4): sd.line((0,y,w,y),fill=(255,255,255))
    im=Image.blend(im,ImageChops.multiply(im,Image.new("RGB",(w,h),(200,200,200))),0.0)
    return im

def glitch_text(im,text,font,cx,cy,off,n=6):
    w,h=im.size
    layer=lambda col,dx: (lambda L:(ImageDraw.Draw(L).text((cx+dx,cy),text,font=font,fill=col+(255,),anchor="mm"),L)[1])(Image.new("RGBA",(w,h),(0,0,0,0)))
    glow=layer(CY,0).filter(ImageFilter.GaussianBlur(off*3))
    im.alpha_composite(glow) if im.mode=="RGBA" else None
    for col,dx in ((MG,-off),(CY,off)):
        L=layer(col,dx); a=L.split()[3].point(lambda v:int(v*0.85)); L.putalpha(a); im.alpha_composite(L)
    main=layer(WH,0)
    # slice displacement
    bb=main.getbbox(); 
    for _ in range(n):
        y0=random.randint(bb[1],bb[3]-4); hh=random.randint(off//2+2,off*2)
        strip=main.crop((0,y0,w,y0+hh)); dx=random.choice([-1,1])*random.randint(off,off*3)
        main.paste((0,0,0,0),(0,y0,w,y0+hh)); main.alpha_composite(strip,(dx if dx>0 else 0,y0),(max(0,-dx),0,w,hh))
    im.alpha_composite(main)

def scan(im,alpha=40):
    w,h=im.size; s=Image.new("RGBA",(w,h),(0,0,0,0)); d=ImageDraw.Draw(s)
    for y in range(0,h,4): d.line((0,y,w,y),fill=(0,0,0,alpha))
    im.alpha_composite(s)

# LOGO 800x800
L=bg(800,800).convert("RGBA")
d=ImageDraw.Draw(L)
d.ellipse((90,90,710,710),outline=CY+(255,),width=6)
d.arc((60,60,740,740),200,340,fill=MG+(255,),width=4)
glitch_text(L,"G",ImageFont.truetype(BLACK,470),400,385,14)
d=ImageDraw.Draw(L)
d.text((400,640),"GLITCHVERSE",font=ImageFont.truetype(BLACK,58),fill=WH+(255,),anchor="mm")
scan(L,45); L.convert("RGB").save("logo_800.png")

# BANNER 2560x1440 (safe 1546x423 centered)
B=bg(2560,1440).convert("RGBA")
glitch_text(B,"GLITCHVERSE",ImageFont.truetype(BLACK,190),1280,665,7,n=2)
d=ImageDraw.Draw(B)
d.text((1280,800),"IS REALITY JUST CODE?",font=ImageFont.truetype(MED,58),fill=CY+(255,),anchor="mm")
d.text((1280,875),"NEW FILE EVERY WEEK  ·  HOSTED BY DR. MIA STERLING",font=ImageFont.truetype(MED,34),fill=(150,165,190,255),anchor="mm")
for x0 in (520,1940):
    d.line((x0,700,x0+100,700),fill=MG+(255,),width=4)
scan(B,35); B.convert("RGB").save("banner_2560x1440.png")
# preview with safe area
P=B.copy(); dp=ImageDraw.Draw(P); dp.rectangle((507,508,2053,931),outline=(255,255,0,255),width=4); P.convert("RGB").resize((1280,720)).save("banner_safe_preview.png")
