import sys
sys.path.insert(0,'../smart')
import lib as L
from PIL import Image, ImageDraw, ImageFilter, ImageFont
W,H=1080,1920
def globe(sz=230):
    S=sz*3; im=Image.new('RGBA',(S,S),(0,0,0,0)); d=ImageDraw.Draw(im)
    w=int(S*0.035); c=S//2; r=int(S*0.40)
    d.ellipse((c-r,c-r,c+r,c+r),outline=(255,255,255,255),width=w)
    for k in (0.45,0.8):
        d.ellipse((c-int(r*k),c-r,c+int(r*k),c+r),outline=(255,255,255,230),width=w//2)
    for yy in (-0.45,0,0.45):
        y=c+int(r*yy); x=int((r**2-(r*yy)**2)**0.5)
        d.line((c-x,y,c+x,y),fill=(255,255,255,230),width=w//2)
    def pin(px,py,s):
        d.ellipse((px-s,py-s,px+s,py+s),fill=(255,255,255,255))
        d.polygon([(px-s*0.85,py+s*0.45),(px+s*0.85,py+s*0.45),(px,py+s*2.1)],fill=(255,255,255,255))
        d.ellipse((px-s*0.38,py-s*0.38,px+s*0.38,py+s*0.38),fill=(0,0,0,0))
    pin(c-int(r*0.35),c-int(r*0.05),int(S*0.075)); pin(c+int(r*0.38),c-int(r*0.32),int(S*0.065))
    d.line((c-int(r*0.30),c+int(r*0.22),c+int(r*0.30),c-int(r*0.02)),fill=(255,255,255,200),width=w//3)
    return im.resize((sz,sz),Image.LANCZOS)
def shadow(img,rad=14,a=150):
    m=img.split()[3].filter(ImageFilter.GaussianBlur(rad))
    sh=Image.new('RGBA',img.size,(0,0,0,0)); sh.putalpha(m.point(lambda v:int(v*a/255)))
    out=Image.new('RGBA',img.size,(0,0,0,0)); out.alpha_composite(sh); out.alpha_composite(img); return out
def label(name,flag,path):
    base=Image.new('RGBA',(W,H),(0,0,0,0))
    g=globe(230)
    f=ImageFont.truetype('/usr/share/fonts/opentype/inter/Inter-Light.otf',150)
    t=L.text_img(name,f)
    fl=L.emoji(flag,120)
    gap=36; tw=t.width+gap+fl.width
    sc=min(1.0,960/tw)
    if sc<1:
        t=t.resize((int(t.width*sc),int(t.height*sc)),Image.LANCZOS); fl=fl.resize((int(fl.width*sc),int(fl.height*sc)),Image.LANCZOS); gap=int(gap*sc); tw=t.width+gap+fl.width
    lay=Image.new('RGBA',(W,H),(0,0,0,0))
    cy=H//2
    lay.alpha_composite(g,(W//2-g.width//2,cy-g.height-30))
    x0=W//2-tw//2
    lay.alpha_composite(t,(x0,cy+10))
    lay.alpha_composite(fl,(x0+t.width+gap,cy+10+(t.height-fl.height)//2+8))
    base.alpha_composite(shadow(lay,18,170)); base.save(path)
def hook(txt,path,em='🤯'):
    base=Image.new('RGBA',(W,H),(0,0,0,0))
    f=ImageFont.truetype('/usr/share/fonts/opentype/inter/Inter-Black.otf',120)
    t=L.text_img(txt,f,fill=(255,228,92),stroke=12,stroke_fill=(0,0,0))
    e=L.emoji(em,130)
    lay=Image.new('RGBA',(W,H),(0,0,0,0))
    tw=t.width+20+e.width; s=min(1.0,980/tw)
    t=t.resize((int(t.width*s),int(t.height*s)),Image.LANCZOS); e=e.resize((int(e.width*s),int(e.height*s)),Image.LANCZOS)
    tw=t.width+20+e.width; x=W//2-tw//2; y=430
    lay.alpha_composite(t,(x,y)); lay.alpha_composite(e,(x+t.width+20,y+(t.height-e.height)//2))
    base.alpha_composite(shadow(lay,16,160)); base.save(path)

C=[('USA','🇺🇸','us'),('PHILIPPINES','🇵🇭','ph'),('THAILAND','🇹🇭','th'),('INDIA','🇮🇳','in'),('INDONESIA','🇮🇩','id'),
('ITALY','🇮🇹','it'),('SPAIN','🇪🇸','es'),('FRANCE','🇫🇷','fr'),('PORTUGAL','🇵🇹','pt'),('SWITZERLAND','🇨🇭','ch'),('NORWAY','🇳🇴','no'),('ICELAND','🇮🇸','is'),
('CROATIA','🇭🇷','hr'),('GERMANY','🇩🇪','de'),('AUSTRIA','🇦🇹','at'),('UK','🇬🇧','gb'),('IRELAND','🇮🇪','ie'),('NETHERLANDS','🇳🇱','nl'),('JAPAN','🇯🇵','jp'),
('CHINA','🇨🇳','cn'),('SOUTH KOREA','🇰🇷','kr'),('NEPAL','🇳🇵','np'),('SRI LANKA','🇱🇰','lk'),('MALAYSIA','🇲🇾','my'),('EGYPT','🇪🇬','eg'),('MOROCCO','🇲🇦','ma'),
('KENYA','🇰🇪','ke'),('SOUTH AFRICA','🇿🇦','za'),('MEXICO','🇲🇽','mx'),('BRAZIL','🇧🇷','br'),('PERU','🇵🇪','pe'),('ARGENTINA','🇦🇷','ar'),('CHILE','🇨🇱','cl'),
('CANADA','🇨🇦','ca'),('AUSTRALIA','🇦🇺','au'),('NEW ZEALAND','🇳🇿','nz'),('JORDAN','🇯🇴','jo'),('OMAN','🇴🇲','om'),('GEORGIA','🇬🇪','ge'),('UZBEKISTAN','🇺🇿','uz'),
('KAZAKHSTAN','🇰🇿','kz'),('RUSSIA','🇷🇺','ru'),('COSTA RICA','🇨🇷','cr'),('BOLIVIA','🇧🇴','bo'),('MONTENEGRO','🇲🇪','me'),('SLOVENIA','🇸🇮','si'),('FINLAND','🇫🇮','fi'),('FIJI','🇫🇯','fj')]
import os
for n,fl,k in C:
    if k not in ('tr','vn','gr','mv','ae','tz'): label(n,fl,f'lab_{k}.png')
hook("DON'T TRY THIS AT HOME!",'hook_a.png','❌')
