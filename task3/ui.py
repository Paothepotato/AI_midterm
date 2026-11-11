from pathlib import Path
import pygame
from kakuro import Puzzle, KakuroSolver

ROOT=Path(__file__).resolve().parent


class KakuroApp:
    BG=(244,243,237); INK=(32,45,45); MUTED=(91,106,105)
    ACCENT=(0,105,96); WHITE=(255,255,251)

    def __init__(self,board='small'):
        pygame.init()
        self.screen=pygame.display.set_mode((1120,790))
        pygame.display.set_caption('Kakuro | Constraint laboratory')
        self.font=pygame.font.SysFont('Segoe UI,Arial',19)
        self.title=pygame.font.SysFont('Segoe UI,Arial',32,bold=True)
        self.digit=pygame.font.SysFont('Segoe UI,Arial',28,bold=True)
        self.mini=pygame.font.SysFont('Segoe UI,Arial',14)
        self.clock=pygame.time.Clock()
        self.board=board; self.interval=160; self.last=0
        self.reset()

    def reset(self):
        self.puzzle=Puzzle.load(ROOT/'data'/f'{self.board}.json')
        self.solver=KakuroSolver(self.puzzle)
        self.stream=self.solver.events()
        self.current=next(self.stream)
        self.playing=False; self.finished=False; self.history=[]; self.steps=0

    def advance(self):
        if self.finished:
            return
        try:
            self.current=next(self.stream)
            self.steps+=1
            cell=self.current['cell']
            self.history.append(self.current['kind']+(f'  r{cell[0]+1} c{cell[1]+1}' if cell else ''))
            if self.current['kind'] in ('done','unsatisfiable'):
                self.finished=True; self.playing=False
        except StopIteration:
            self.finished=True; self.playing=False

    def text(self,value,pos,color=None,font=None):
        self.screen.blit((font or self.font).render(str(value),True,color or self.INK),pos)

    def buttons(self):
        return [(pygame.Rect(750,220+i*48,322,38),label,action) for i,(label,action) in enumerate([
            ('Next step   [Right]','next'),
            ('Pause   [Space]' if self.playing else 'Play   [Space]','play'),
            ('Reset   [R]','reset'),('Switch board   [Tab]','switch'),
            (f'Speed: {1000/self.interval:.1f} steps/s   [+ / -]','speed')])]

    def action(self,name):
        if name=='next': self.playing=False; self.advance()
        elif name=='play' and not self.finished: self.playing=not self.playing
        elif name=='reset': self.reset()
        elif name=='switch':
            boards=['small','large','backtrack_demo']
            self.board=boards[(boards.index(self.board)+1)%len(boards)]; self.reset()
        elif name=='speed': self.interval=80 if self.interval==160 else 160

    def draw(self):
        self.screen.fill(self.BG)
        self.text('CONSTRAINT LABORATORY / TASK 03',(32,20),self.ACCENT,self.mini)
        self.text('Kakuro',(32,44),font=self.title)
        self.text(self.puzzle.name,(32,91),self.MUTED)
        n=len(self.puzzle.grid); size=min(112,590//n); x0,y0=32,140
        colors={'propagate':(203,235,225),'assign':(252,224,166),
                'backtrack':(249,207,199),'contradiction':(249,207,199)}
        for r,row in enumerate(self.puzzle.grid):
            for c,clue in enumerate(row):
                rect=pygame.Rect(x0+c*size,y0+r*size,size,size)
                if clue is not None:
                    pygame.draw.rect(self.screen,self.INK,rect)
                    if clue:
                        pygame.draw.line(self.screen,(131,149,147),rect.topleft,rect.bottomright,1)
                        if 'down' in clue: self.text(clue['down'],(rect.x+7,rect.bottom-26),self.WHITE)
                        if 'right' in clue: self.text(clue['right'],(rect.right-30,rect.y+5),self.WHITE)
                else:
                    fill=self.WHITE
                    if (r,c)==self.current['cell']:
                        fill=colors.get(self.current['kind'],(203,235,225))
                    pygame.draw.rect(self.screen,fill,rect)
                    domain=self.current['domains'][(r,c)]
                    if len(domain)==1:
                        surf=self.digit.render(str(next(iter(domain))),True,self.ACCENT)
                        self.screen.blit(surf,surf.get_rect(center=rect.center))
                    else:
                        for v in sorted(domain):
                            dx,dy=(v-1)%3,(v-1)//3
                            self.text(v,(rect.x+8+dx*(size-12)//3,rect.y+6+dy*(size-12)//3),self.MUTED,self.mini)
                pygame.draw.rect(self.screen,self.BG,rect,1)
        self.text('SEARCH STATE',(750,140),self.ACCENT,self.mini)
        self.text(self.current['kind'].upper(),(750,165),font=self.digit)
        for rect,label,action in self.buttons():
            hover=rect.collidepoint(pygame.mouse.get_pos())
            pygame.draw.rect(self.screen,(219,230,224) if hover else (231,232,223),rect,border_radius=5)
            self.text(label,(rect.x+12,rect.y+7))
        stats=self.solver.stats
        self.text(f"Nodes {stats['nodes']} / Backtracks {stats['backtracks']}",(750,475))
        self.text(f"Pruned {stats['pruned']} / Depth {self.current['depth']}",(750,505))
        self.text('RECENT EVENTS',(750,557),self.ACCENT,self.mini)
        for i,line in enumerate(self.history[-5:]): self.text(line,(750,582+i*25),self.MUTED)
        self.text('Green: propagation   /   Amber: assignment   /   Red: backtrack',(32,755),self.MUTED,self.mini)
        pygame.display.flip()

    def run(self,screenshot=None):
        if screenshot:
            for _ in range(8): self.advance()
            self.draw(); pygame.image.save(self.screen,str(screenshot)); pygame.quit(); return
        running=True
        while running:
            for event in pygame.event.get():
                if event.type==pygame.QUIT: running=False
                elif event.type==pygame.KEYDOWN:
                    keymap={pygame.K_RIGHT:'next',pygame.K_SPACE:'play',pygame.K_r:'reset',pygame.K_TAB:'switch'}
                    if event.key in keymap: self.action(keymap[event.key])
                    elif event.key in (pygame.K_EQUALS,pygame.K_PLUS): self.interval=max(16,self.interval//2)
                    elif event.key==pygame.K_MINUS: self.interval=min(2000,self.interval*2)
                    elif event.key==pygame.K_ESCAPE: running=False
                elif event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
                    for rect,label,action in self.buttons():
                        if rect.collidepoint(event.pos): self.action(action)
            now=pygame.time.get_ticks()
            if self.playing and now-self.last>=self.interval:
                self.advance(); self.last=now
            self.draw(); self.clock.tick(60)
        pygame.quit()
