"""
AI 데스크탑 펫 - AppKit 네이티브 (PyObjC)
버튼 정밀 위치 + 호버/프레스 효과 + 커서 변경
"""
import objc
import math, random, time, os, threading
from Foundation import NSObject, NSTimer, NSDate, NSMakeRect
from AppKit import (
    NSApplication, NSApp, NSWindow, NSView, NSColor, NSImage,
    NSBezierPath, NSFont,
    NSEvent, NSBorderlessWindowMask, NSFloatingWindowLevel,
    NSBackingStoreBuffered,
    NSFontAttributeName, NSForegroundColorAttributeName,
    NSCursor, NSTrackingArea,
    NSTrackingMouseMoved, NSTrackingActiveAlways, NSTrackingInVisibleRect,
)

# ── 경로 ─────────────────────────────────────────────────────────────
def here(name):
    d = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(d, name)

# ── 레이아웃 ─────────────────────────────────────────────────────────
BASE_W, BASE_H = 300.0, 383.0

LCD_RX, LCD_RY = 116/420, 178/537
LCD_RW, LCD_RH = 190/420, 185/537

# 각 버튼별 (중심x비율, 중심y비율_nsview기준, 반지름px@300px)
BTNS = [
    (0.3050, 0.1608, 16),   # ■ 왼쪽  = 전원
    (0.5011, 0.1361, 16),   # ▶ 가운데 = 다음 메시지
    (0.7000, 0.1600, 16),   # ● 오른쪽 = 춤추기
]

# ── 메시지 ───────────────────────────────────────────────────────────
MSG_IDLE   = ["혹시 자고있어?","20분째 멍때리는중","나 여기 있잖아!","딴짓하고 있지?","뭔가 좀 해줘~","심심해 죽겠다","슬슬 움직여봐!"]
MSG_RANDOM = ["오늘도 화이팅!","밥은 먹었어?","물 한 잔 마셔!","눈 피로하지 않아?","스트레칭 해봐~","잠깐 쉬어가!","잘하고 있어!","나랑 놀자~","집중 멋진데?","커피 한 잔?","퇴근 생각나지?","나 보고 싶었지?","생산성 MAX!","조금만 더!","오늘도 수고해!"]
MSG_HELLO  = ["안녕!","켜줘서 고마워~","나야나!","같이 일하자!"]
MSG_BYE    = ["잘가...","또 켜줘!","수고했어~","안뇽!"]


class PetView(NSView):
    def initWithFrame_(self, frame):
        self = objc.super(PetView, self).initWithFrame_(frame)
        if self is None: return None

        self.scale      = 1.0
        self.animT      = 0.0
        self.mode       = 'idle'
        self.bubble     = ''
        self.isOff      = False
        self.danceEnd   = 0.0
        self.idleSince  = time.time()
        self.idleWarned = False
        self.nextAuto   = time.time() + random.uniform(30, 70)
        self.msgPool    = list(MSG_RANDOM)
        random.shuffle(self.msgPool)
        self.msgIdx     = 0
        self.drag_pos   = None
        self.hoveredBtn = -1
        self.pressedBtn = -1

        # 이미지
        self.bodyImg = NSImage.alloc().initWithContentsOfFile_(here('tamagochi.png'))
        self.petImg  = NSImage.alloc().initWithContentsOfFile_(here('pet.png'))

        # 폰트
        fp = here('PFStardust.ttf')
        if os.path.exists(fp):
            from CoreText import CTFontManagerRegisterFontsForURL
            from Foundation import NSURL
            url = NSURL.fileURLWithPath_(fp)
            CTFontManagerRegisterFontsForURL(url, 0, None)
            self.font = NSFont.fontWithName_size_('PFStardust', 15) or NSFont.boldSystemFontOfSize_(12)
        else:
            self.font = NSFont.fontWithName_size_('AppleGothic', 14) or NSFont.boldSystemFontOfSize_(13)

        # 마우스 이동 트래킹
        opts = NSTrackingMouseMoved | NSTrackingActiveAlways | NSTrackingInVisibleRect
        area = NSTrackingArea.alloc().initWithRect_options_owner_userInfo_(
            self.bounds(), opts, self, None)
        self.addTrackingArea_(area)

        # 30fps 타이머
        NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            1/30.0, self, 'tick:', None, True)

        # 인사
        self.setMsg_(random.choice(MSG_HELLO))
        threading.Timer(4.0, self.clearMsg).start()

        return self

    # ── 버튼 히트 테스트 ─────────────────────────────────────────────
    @objc.python_method
    def btnHit(self, loc):
        w = self.bounds().size.width
        h = self.bounds().size.height
        scale = w / BASE_W
        for i, (rx, ry, rr) in enumerate(BTNS):
            bx = rx * w
            by = ry * h
            r  = rr * scale
            if math.hypot(loc.x - bx, loc.y - by) < r:
                return i
        return -1

    # ── 메시지 ───────────────────────────────────────────────────────
    @objc.python_method
    def nextMsg(self):
        m = self.msgPool[self.msgIdx % len(self.msgPool)]
        self.msgIdx += 1
        return m

    @objc.python_method
    def setMsg_(self, txt):
        self.bubble = txt
        self.mode   = 'talking'
        self.setNeedsDisplay_(True)

    def clearMsg(self):
        self.bubble = ''
        if self.mode == 'talking': self.mode = 'idle'
        self.setNeedsDisplay_(True)

    def powerOff(self):
        self.isOff  = True
        self.mode   = 'off'
        self.bubble = ''
        self.setNeedsDisplay_(True)

    @objc.python_method
    def onBtn_(self, i):
        if i == 0:
            if self.isOff:
                self.isOff = False; self.mode = 'idle'
                self.setMsg_(random.choice(MSG_HELLO))
                threading.Timer(4.0, self.clearMsg).start()
            else:
                self.setMsg_(random.choice(MSG_BYE))
                threading.Timer(1.5, self.powerOff).start()
        elif i == 1:
            if not self.isOff:
                self.setMsg_(self.nextMsg())
                threading.Timer(5.0, self.clearMsg).start()
        elif i == 2:
            if not self.isOff:
                self.clearMsg()
                self.mode     = 'dancing'
                self.danceEnd = time.time() + 4.0

    # ── 타이머 ───────────────────────────────────────────────────────
    def tick_(self, timer):
        self.animT += 1/30.0
        now = time.time()
        if self.mode == 'dancing' and now > self.danceEnd:
            self.mode = 'idle'
        if now - self.idleSince > 20*60 and not self.idleWarned:
            self.idleWarned = True
            self.setMsg_(random.choice(MSG_IDLE))
            threading.Timer(10.0, self.clearMsg).start()
        if now > self.nextAuto and not self.isOff and self.mode == 'idle':
            self.setMsg_(self.nextMsg())
            threading.Timer(7.0, self.clearMsg).start()
            self.nextAuto = now + random.uniform(40, 100)
        self.setNeedsDisplay_(True)

    # ── 그리기 ───────────────────────────────────────────────────────
    def drawRect_(self, rect):
        w = self.bounds().size.width
        h = self.bounds().size.height

        # 투명 배경
        NSColor.clearColor().set()
        NSBezierPath.fillRect_(self.bounds())

        # 본체
        if self.bodyImg:
            self.bodyImg.drawInRect_fromRect_operation_fraction_(
                self.bounds(), NSMakeRect(0,0,0,0), 2, 1.0)

        # 버튼 호버/프레스 오버레이
        self.drawBtnEffects_(w, h)

        # LCD
        lx = LCD_RX * w
        ly = h - (LCD_RY + LCD_RH) * h
        lw = LCD_RW * w
        lh = LCD_RH * h
        lcdRect = NSMakeRect(lx, ly, lw, lh)

        if self.mode == 'off':
            NSColor.colorWithRed_green_blue_alpha_(0.1, 0.11, 0.07, 1).set()
            NSBezierPath.fillRect_(lcdRect)
            return

        NSColor.colorWithRed_green_blue_alpha_(0.92, 0.91, 0.76, 1).set()
        NSBezierPath.fillRect_(lcdRect)

        # 펫
        if self.petImg:
            pw = lw * 0.50
            ph = lh * 0.50
            bob = math.sin(self.animT * 2.5) * 3
            px  = lx + (lw - pw) / 2
            # 모든 모드에서 동일한 Y 위치 (가운데 고정)
            py  = ly + (lh - ph) / 2 + bob

            if self.mode == 'dancing':
                sc  = 1.0 + 0.1 * abs(math.sin(self.animT * 10))
                shk = math.sin(self.animT * 18) * 6
                pw2 = pw * sc; ph2 = ph * sc
                px  = lx + (lw - pw2) / 2 + shk
                py  = ly + (lh - ph2) / 2 + bob
                pw, ph = pw2, ph2
            elif self.mode == 'talking':
                # 말풍선 있어도 위치 그대로 유지
                tb = math.sin(self.animT * 9) * 2
                py = ly + (lh - ph) / 2 + bob - 30

            self.petImg.drawInRect_fromRect_operation_fraction_(
                NSMakeRect(px, py, pw, ph), NSMakeRect(0,0,0,0), 2, 1.0)

        # 말풍선
        if self.bubble and self.mode == 'talking':
            self.drawBubble_(lcdRect)

    @objc.python_method
    def drawBtnEffects_(self, w, h):
        """각 버튼 위치/크기에 맞는 호버·프레스 원 오버레이"""
        scale = w / BASE_W
        for i, (rx, ry, rr) in enumerate(BTNS):
            bx = rx * w
            by = ry * h
            r  = rr * scale

            if i == self.pressedBtn:
                NSColor.colorWithRed_green_blue_alpha_(0, 0, 0, 0.05).set()
                path = NSBezierPath.bezierPath()
                path.appendBezierPathWithOvalInRect_(
                    NSMakeRect(bx - r, by - r, r*2, r*2))
                path.fill()
            elif i == self.hoveredBtn:
                NSColor.colorWithRed_green_blue_alpha_(1, 1, 1, 0.05).set()
                path = NSBezierPath.bezierPath()
                path.appendBezierPathWithOvalInRect_(
                    NSMakeRect(bx - r, by - r, r*2, r*2))
                path.fill()

    @objc.python_method
    def drawBubble_(self, lcdRect):
        attrs = {
            NSFontAttributeName: self.font,
            NSForegroundColorAttributeName: NSColor.blackColor()
        }
        ns_txt = objc.lookUpClass('NSString').stringWithString_(self.bubble)
        sz  = ns_txt.sizeWithAttributes_(attrs)
        pad = 8.0
        bw  = min(sz.width + pad*2, lcdRect.size.width - 8)
        bh  = sz.height + pad*2
        bx  = lcdRect.origin.x + (lcdRect.size.width - bw) / 2
        by  = lcdRect.origin.y + lcdRect.size.height - bh - 6

        path = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
            NSMakeRect(bx, by, bw, bh), 6, 6)
        NSColor.colorWithRed_green_blue_alpha_(0.92, 0.91, 0.76, 1).set()
        path.fill()
        NSColor.colorWithRed_green_blue_alpha_(0.2, 0.2, 0.14, 1).set()
        path.setLineWidth_(1)
        path.stroke()

        # 꼬리
        tx = bx + bw / 2
        ty = by
        tail = NSBezierPath.bezierPath()
        tail.moveToPoint_((tx-5, ty))
        tail.lineToPoint_((tx+5, ty))
        tail.lineToPoint_((tx,   ty-8))
        tail.closePath()
        NSColor.colorWithRed_green_blue_alpha_(0.92, 0.91, 0.76, 1).set()
        tail.fill()
        NSColor.colorWithRed_green_blue_alpha_(0.2, 0.2, 0.14, 1).set()
        tail.stroke()

        ns_txt.drawAtPoint_withAttributes_(
            (bx + (bw - sz.width)/2, by + (bh - sz.height)/2), attrs)

    # ── 마우스 이벤트 ────────────────────────────────────────────────
    def mouseDown_(self, event):
        loc = self.convertPoint_fromView_(event.locationInWindow(), None)
        i   = self.btnHit(loc)
        if i >= 0:
            self.pressedBtn = i
            self.setNeedsDisplay_(True)
            return
        self.drag_pos  = event.locationInWindow()
        self.idleSince = time.time()

    def mouseUp_(self, event):
        loc = self.convertPoint_fromView_(event.locationInWindow(), None)
        i   = self.btnHit(loc)
        if self.pressedBtn >= 0:
            if i == self.pressedBtn:
                self.onBtn_(self.pressedBtn)
            self.pressedBtn = -1
            self.setNeedsDisplay_(True)
            return
        self.drag_pos = None

    def mouseDragged_(self, event):
        if not self.drag_pos: return
        win = self.window()
        dx  = event.locationInWindow().x - self.drag_pos.x
        dy  = event.locationInWindow().y - self.drag_pos.y
        org = win.frame().origin
        win.setFrameOrigin_((org.x + dx, org.y + dy))

    def mouseMoved_(self, event):
        loc  = self.convertPoint_fromView_(event.locationInWindow(), None)
        prev = self.hoveredBtn
        self.hoveredBtn = self.btnHit(loc)
        if self.hoveredBtn >= 0:
            NSCursor.pointingHandCursor().set()
        else:
            NSCursor.arrowCursor().set()
        if self.hoveredBtn != prev:
            self.setNeedsDisplay_(True)

    def mouseExited_(self, event):
        self.hoveredBtn = -1
        NSCursor.arrowCursor().set()
        self.setNeedsDisplay_(True)

    def scrollWheel_(self, event):
        delta = event.scrollingDeltaY()
        self.scale = max(0.4, min(2.5, self.scale + delta * 0.01))
        ww = BASE_W * self.scale
        wh = BASE_H * self.scale
        if self.window():
            self.window().setContentSize_((ww, wh))
            self.setFrame_(NSMakeRect(0, 0, ww, wh))

    def resetCursorRects(self):
        self.discardCursorRects()
        w = self.bounds().size.width
        h = self.bounds().size.height
        scale = w / BASE_W
        for rx, ry, rr in BTNS:
            r    = rr * scale
            rect = NSMakeRect(rx*w - r, ry*h - r, r*2, r*2)
            self.addCursorRect_cursor_(rect, NSCursor.pointingHandCursor())

    def acceptsFirstResponder(self): return True
    def isFlipped(self):            return False


# ── 실행 ─────────────────────────────────────────────────────────────
def main():
    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(1)  # Dock 숨김

    win = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
        NSMakeRect(500, 500, BASE_W, BASE_H),
        NSBorderlessWindowMask,
        NSBackingStoreBuffered,
        False
    )
    win.setOpaque_(False)
    win.setBackgroundColor_(NSColor.clearColor())
    win.setHasShadow_(False)
    win.setLevel_(0)
    win.setCollectionBehavior_(1 | 16)

    view = PetView.alloc().initWithFrame_(NSMakeRect(0, 0, BASE_W, BASE_H))
    win.setContentView_(view)
    win.makeFirstResponder_(view)
    win.makeKeyAndOrderFront_(None)

    NSApp.activateIgnoringOtherApps_(True)
    app.run()


if __name__ == '__main__':
    import traceback
    try:
        main()
    except Exception as e:
        traceback.print_exc()
        input("에러 확인 후 Enter...")
