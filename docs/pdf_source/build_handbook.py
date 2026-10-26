"""Build the beginner PDF using ReportLab. No R analysis is performed here."""
from pathlib import Path
import json, html, re, sys
from xml.sax.saxutils import escape
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, Image, Preformatted, KeepTogether, Flowable, Frame

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path(__file__).parent
OUT = ROOT / 'output/pdf/GSE174574_RStudio_零基础复现手册.pdf'
OUT.parent.mkdir(parents=True, exist_ok=True)
pdfmetrics.registerFont(TTFont('CJK', 'C:/Windows/Fonts/msyh.ttc', subfontIndex=0))
pdfmetrics.registerFont(TTFont('CJKB', 'C:/Windows/Fonts/msyhbd.ttc', subfontIndex=0))
pdfmetrics.registerFont(TTFont('Code', 'C:/Windows/Fonts/consola.ttf'))
pdfmetrics.registerFontFamily('CJK', normal='CJK', bold='CJKB', italic='CJK', boldItalic='CJKB')
NAVY = colors.HexColor('#17324D'); TEAL = colors.HexColor('#137E84')
GRAY = colors.HexColor('#586A78'); PALE = colors.HexColor('#EAF4F5')
W,H = A4; LEFT=43; WIDTH=W-86; TOP=H-112; BOTTOM=47
styles = {
 'body': ParagraphStyle('body', fontName='CJK', fontSize=10.2, leading=17.2, textColor=NAVY, wordWrap='CJK', spaceAfter=8),
 'small': ParagraphStyle('small', fontName='CJK', fontSize=8.6, leading=13.5, textColor=GRAY, wordWrap='CJK', spaceAfter=6),
 'sub': ParagraphStyle('sub', fontName='CJKB', fontSize=12.8, leading=19, textColor=TEAL, spaceBefore=7, spaceAfter=7, wordWrap='CJK'),
 'cell': ParagraphStyle('cell', fontName='CJK', fontSize=9.2, leading=14.5, textColor=NAVY, wordWrap='CJK'),
 'cellhead': ParagraphStyle('cellhead', fontName='CJKB', fontSize=9.2, leading=14.5, textColor=colors.white, wordWrap='CJK'),
 'code': ParagraphStyle('code', fontName='Code', fontSize=8.3, leading=12, textColor=colors.HexColor('#102D46'), backColor=colors.HexColor('#F1F4F7'), borderPadding=9, spaceBefore=4, spaceAfter=12),
}

def P(text, kind='body'):
    text = escape(text).replace('\n','<br/>')
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    return Paragraph(text, styles[kind])

def code(text, size=None):
    st=styles['code'].clone('codeblock')
    if size: st.fontSize=size; st.leading=size*1.45
    # Keep physical lines intact so copied code is not silently changed.
    for line in text.splitlines():
        if pdfmetrics.stringWidth(line, 'Code', st.fontSize)>WIDTH-24:
            raise ValueError('Code line too long: '+line)
    return [Spacer(1,3),Preformatted(text, st),Spacer(1,4)]

def table(rows, widths=None):
    if widths is None: widths=[WIDTH/len(rows[0])]*len(rows[0])
    else: widths=[WIDTH*w/sum(widths) for w in widths]
    data=[[P(str(x), 'cellhead' if i==0 else 'cell') for x in r] for i,r in enumerate(rows)]
    t=Table(data,colWidths=widths,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),NAVY),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.HexColor('#F2F6F8'),colors.white]),('LINEBELOW',(0,0),(-1,-1),.3,colors.HexColor('#DCE5EA'))]))
    return t

def callout(label, text):
    t=Table([[P(label,'sub')],[P(text)]],colWidths=[WIDTH])
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),PALE),('LEFTPADDING',(0,0),(-1,-1),12),('RIGHTPADDING',(0,0),(-1,-1),12),('TOPPADDING',(0,0),(-1,0),3),('BOTTOMPADDING',(0,-1),(-1,-1),5)]))
    return [Spacer(1,5),t,Spacer(1,10)]

def figure(path, maxheight=300):
    from PIL import Image as PILImage
    f=ROOT/path
    with PILImage.open(f) as im: iw,ih=im.size
    scale=min(WIDTH/iw,maxheight/ih)
    return Image(str(f), width=iw*scale, height=ih*scale, hAlign='CENTER')

class PaneMap(Flowable):
    def __init__(self): super().__init__();self.width=WIDTH;self.height=292
    def draw(self):
        c=self.canv; w=WIDTH
        c.setFillColor(colors.HexColor('#E8EEF4'));c.roundRect(0,0,w,292,5,fill=1,stroke=0)
        c.setFont('Code',9);c.setFillColor(NAVY);c.drawString(10,275,'File  Edit  Code  View  Plots  Session  Tools  Help')
        panes=[(8,143,w*.60-12,120,'1  Source / 脚本编辑区','Run   |   Source'),(8,8,w*.60-12,129,'2  Console / 执行与输出区','> 1 + 1   [1] 2'),(w*.60+3,143,w*.40-11,120,'3  Environment / 对象区','obj   qc_table   p_umap'),(w*.60+3,8,w*.40-11,129,'4  Files / Plots / 输出区','Files | Plots | Packages | Help')]
        for x,y,pw,ph,title,sub in panes:
            c.setFillColor(colors.white);c.roundRect(x,y,pw,ph,3,fill=1,stroke=0)
            c.setFillColor(TEAL);c.setFont('CJKB',9);c.drawString(x+8,y+ph-18,title)
            c.setFont('CJK',8);c.setFillColor(GRAY);c.drawString(x+8,y+ph-39,sub)
        c.setFillColor(GRAY);c.setFont('CJK',8);c.drawString(16,158,'写代码；选中后 Ctrl+Enter 运行')
        c.drawString(16,76,'这里的 > 是提示符，不要复制进脚本')
        c.drawString(w*.60+10,187,'对象存在内存中，不等于已保存')
        c.drawString(w*.60+10,53,'Files 看文件；Plots 看交互图')

class Workflow(Flowable):
    def __init__(self):super().__init__();self.width=WIDTH;self.height=220
    def draw(self):
        c=self.canv
        labels=['官方计数矩阵','质控与每样本抽样','标准化 / 高变基因','PCA / 聚类 / UMAP','多标记细胞注释','样本伪 bulk / edgeR']
        for i,lab in enumerate(labels):
            x=(i%2)*(WIDTH/2+3);y=153-(i//2)*70
            c.setFillColor(PALE if i%2==0 else colors.HexColor('#F2F4F8'));c.roundRect(x,y,WIDTH/2-7,49,5,fill=1,stroke=0)
            c.setFont('CJKB',11);c.setFillColor(TEAL);c.drawString(x+11,y+29,f'{i+1:02d}')
            c.setFont('CJK',10);c.setFillColor(NAVY);c.drawString(x+42,y+27,lab)

def render_block(b):
    kind=b['type']
    if kind=='p': return [P(b['text'],b.get('style','body'))]
    if kind=='sub': return [P(b['text'],'sub')]
    if kind=='code': return code(b['text'],b.get('size'))
    if kind=='table':return [table(b['rows'],b.get('widths')),Spacer(1,10)]
    if kind=='callout':return callout(b['label'],b['text'])
    if kind=='figure':return [figure(b['path'],b.get('height',300)),Spacer(1,7),P(b.get('caption',''),'small')]
    if kind=='panemap':return [PaneMap(),Spacer(1,9)]
    if kind=='workflow':return [Workflow(),Spacer(1,9)]
    if kind=='link':return [Paragraph('<a href="'+html.escape(b['url'],quote=True)+'" color="#137E84">'+escape(b['label'])+'</a>',styles['body'])]
    if kind=='sourcecode':
        delimiter=b.get('split','__NO_SPLIT__');part=b.get('part',0)
        source=(ROOT/b['path']).read_text(encoding='utf-8').split(delimiter)[part]
        if part>0:source=delimiter+source
        return code(source.strip(),b.get('size',8.3))
    raise ValueError(kind)

def build():
    pages=json.loads((SOURCE/'handbook_content.json').read_text(encoding='utf-8'))
    c=canvas.Canvas(str(OUT),pagesize=A4,pageCompression=1)
    c.setTitle('GSE174574 脑缺血单细胞 - RStudio 零基础复现手册')
    c.setAuthor('onlyone-hash | Reproducible educational reanalysis')
    c.setSubject('RStudio interface, beginner steps, Seurat, pseudobulk, visualization')
    layout=[]
    for i,page in enumerate(pages,1):
        c.bookmarkPage('page'+str(i));c.addOutlineEntry(page['title'],'page'+str(i),level=0,closed=False)
        c.setFillColor(TEAL);c.rect(0,H-8,W,8,fill=1,stroke=0)
        c.setFillColor(GRAY);c.setFont('CJK',8.1);c.drawString(LEFT,H-31,'GSE174574  /  RStudio 零基础复现手册')
        c.drawRightString(W-LEFT,H-31,page.get('section','操作 · 理解 · 核查'))
        c.setFont('CJKB',19);c.setFillColor(NAVY)
        title=Paragraph(page['title'],ParagraphStyle('title',fontName='CJKB',fontSize=19,leading=27,textColor=NAVY,wordWrap='CJK'))
        tw,th=title.wrap(WIDTH,70);title.drawOn(c,LEFT,H-55-th)
        top=H-65-th
        c.setStrokeColor(colors.HexColor('#DAE5EA'));c.line(LEFT,39,W-LEFT,39)
        c.setFillColor(GRAY);c.setFont('CJK',8);c.drawString(LEFT,25,'教学抽样版 · R 4.4.1 基准 · 2026-10-26')
        c.drawRightString(W-LEFT,25,f'{i:02d} / {len(pages):02d}')
        blocks=[]
        for b in page['blocks']:blocks.extend(render_block(b))
        f=Frame(LEFT,BOTTOM,WIDTH,top-BOTTOM,leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)
        f.addFromList(blocks,c)
        if blocks:raise RuntimeError(f'Page {i} overflows: {page["title"]}; remaining {len(blocks)} blocks')
        layout.append({'page':i,'title':page['title']})
        c.showPage()
    c.save()
    (ROOT/'tmp/pdfs/page_index.json').write_text(json.dumps(layout,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'pdf':str(OUT),'pages':len(pages),'bytes':OUT.stat().st_size},ensure_ascii=False))

if __name__=='__main__':build()
