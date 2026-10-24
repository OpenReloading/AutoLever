"""Browser checks for the Markdown pages and their BuildGuide components. Requires Playwright + Chromium.
Run against the built site served under /AutoLever/ (AGENTS.md): python tests/check_guide.py http://127.0.0.1:8000/AutoLever
"""
import csv
import io
import json
import re
import sys
import tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

BASE=(sys.argv[1] if len(sys.argv)>1 else 'http://127.0.0.1:8000').rstrip('/')
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,args=['--no-sandbox'])
    context=browser.new_context(viewport={'width':1440,'height':1000},accept_downloads=True)
    context.route('**/*',lambda r:r.continue_() if r.request.url.startswith(BASE) else r.abort())
    page=context.new_page();errors=[];missing=[];external=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('response',lambda r:missing.append(r.url) if r.status>=400 else None)
    # no third-party requests (fonts, CDNs): the route below would only hide them
    page.on('request',lambda r:external.append(r.url) if r.url.startswith(('http://','https://')) and not r.url.startswith(BASE) else None)
    def go(path=''):
        page.goto(BASE+'/'+path,wait_until='domcontentloaded')
        expect(page.locator('.ag-guide' if path else 'main h1')).to_be_visible()
    def ready():
        expect(page.locator('.ag-board-canvas')).to_have_attribute('data-ready','true')
    go('wiring/')
    data=json.loads(page.locator('#guide-data').text_content())
    wiring,tubing,bom=data['boards']['wiring']['steps'],data['boards']['tubing']['steps'],data['bom']['items']
    assert sorted(data)==['boards','bom','storage'],sorted(data)   # components only: no pages, intro, brand or warning
    index=Path(__file__).parent.parent.joinpath('docs/index.md').read_text(encoding='utf-8')
    # The introduction is plain Markdown: title, lead and sections of docs/index.md.
    go()
    expect(page.locator('main h1')).to_have_text(re.search(r'^# (.+)$',index,re.M)[1])
    expect(page.locator('main h2')).to_have_text(re.findall(r'^## (.+)$',index,re.M))
    expect(page.locator('.md-content__inner > p').first).to_contain_text('Lee APP')
    expect(page.locator('.ag-guide')).to_have_count(0)
    expect(page.locator('.md-tabs__link')).to_have_text(['Introduction','BOM','Wiring','Tubing'])
    # The safety admonition sits under the title on every page, without exact figures: full text on the introduction and BOM, short with a link on wiring and tubing.
    for path,full in [('',True),('bom/',True),('wiring/',False),('tubing/',False)]:
        go(path)
        warning=page.locator('main h1 + .admonition.danger')
        expect(warning).to_have_count(1)
        expect(warning.locator('.admonition-title')).to_have_text('Safety')
        expect(warning).to_contain_text('E-STOP is not a safety-rated')
        expect(warning).not_to_contain_text(re.compile(r'\d+ ?(N|bar)\b'))
        if full:
            expect(warning).to_contain_text('Household electricity')
            expect(warning.locator('a')).to_have_count(0)
        else:
            expect(warning).not_to_contain_text('Household electricity')
            expect(warning.locator('a')).to_have_attribute('href','../')
    # Real page navigation, reload and browser back preserve the destination.
    for name,slug in [('BOM','bom'),('Wiring','wiring'),('Tubing','tubing')]:
        page.locator('.md-tabs').get_by_role('link',name=name,exact=True).click()
        expect(page).to_have_url(BASE+'/'+slug+'/')
        page.reload(wait_until='domcontentloaded')
        expect(page.locator('main h1')).to_have_text(name)
        expect(page.locator('.admonition.danger')).to_be_visible()
    page.go_back(wait_until='domcontentloaded')
    expect(page.locator('main h1')).to_have_text('Wiring')
    # Every board connection matches the validated source, with no extra diode wires.
    for step in wiring:
        for wire in step['connections']:
            go(f"wiring/#wiring={step['id']}/{wire['no']}");ready()
            expect(page.locator('.ag-connection-detail')).to_contain_text(wire['la'])
            expect(page.locator('.ag-connection-detail')).to_contain_text(wire['lb'])
            expect(page.locator('[data-connection]')).to_have_count(len(step['connections']))
            expect(page.locator('[data-connection="'+wire['no']+'"]')).to_have_attribute('aria-label',wire['no']+': '+wire['la']+' to '+wire['lb']+('; ring at '+wire['la'] if wire['color']=='DIODE' else ''))
    # Each wiring step shows its own note, and the note changes with the step.
    assert all(s['note'] for s in wiring)
    for step in wiring:
        go(f"wiring/#wiring={step['id']}/{step['connections'][0]['no']}");ready()
        expect(page.locator('.ag-step-note')).to_have_text(step['note'])
    # Each tubing step shows its tube text and check.
    assert all(s['note'] for s in tubing)
    for step in tubing:
        go(f"tubing/#tubing={step['id']}");ready()
        expect(page.locator('.ag-step-note')).to_have_text(step['note'])
    go('wiring/#wiring=A/1');ready()
    page.locator('[data-role=scope]').select_option('single');ready()
    expect(page.locator('[data-connection]')).to_have_count(1)
    page.locator('[data-role=scope]').select_option('all');ready()
    expect(page.locator('[data-connection]')).to_have_count(sum(len(s['connections']) for s in wiring))
    page.locator('[data-role=scope]').select_option('step');ready()
    page.locator('.ag-verify input').check()
    expect(page.locator('.ag-wire-row.selected input')).to_be_checked()
    page.reload(wait_until='domcontentloaded')
    expect(page.locator('.ag-verify input')).to_be_checked()
    page.locator('[data-action=next-wire]').click()
    expect(page.locator('.ag-wire-row.selected .ag-wire-number')).to_have_text('2')
    expect(page.locator('.ag-verify input')).not_to_be_checked()
    # A tick belongs to one exact connection: a tick for wire 16 with other ends stays unchecked, the real key is checked.
    c16=next(c for st in wiring for c in st['connections'] if c['no']=='16')
    for key,done in [(f"wire-16:{c16['a']}:X",False),(f"wire-16:{c16['a']}:{c16['b']}",True)]:
        page.evaluate("key=>localStorage.setItem('autolever-guide',JSON.stringify({[key]:true}))",key)
        go('wiring/#wiring=C/16');page.reload(wait_until='domcontentloaded');ready()   # same URL: goto alone keeps the old state
        (expect(page.locator('.ag-verify input')).to_be_checked if done else expect(page.locator('.ag-verify input')).not_to_be_checked)()
    go('wiring/#wiring=A/1')
    page.locator('[data-action=prev-wire]').click()
    expect(page.locator('.ag-wire-row.selected .ag-wire-number')).to_have_text(wiring[0]['connections'][-1]['no'])
    go('wiring/#wiring=H/'+wiring[-1]['connections'][-1]['no'])
    expect(page.locator('[data-action=next-wire]')).to_be_disabled()   # the last connection of the board: the page, not the component, links on
    # Tubing has the same workspace, zoom, scope, selection and fullscreen controls.
    for step in tubing:
        tube=step['connections'][0]
        go(f"tubing/#tubing={step['id']}");ready()
        expect(page.locator('.ag-connection-detail')).to_contain_text(tube['la'])
        expect(page.locator('.ag-connection-detail')).to_contain_text(tube['lb'])
        expect(page.locator('[data-connection]')).to_have_count(len(tubing))   # tubing shows every connection by default
        page.locator('.ag-verify input').check()
    page.reload(wait_until='domcontentloaded')
    tubes=len(tubing)
    expect(page.locator('.ag-progress')).to_have_text(f'{tubes} / {tubes} checked')
    expect(page.locator('[data-action=next-wire]')).to_be_disabled()
    page.locator('[data-role=scope]').select_option('all');ready()
    expect(page.locator('[data-connection]')).to_have_count(tubes)
    page.locator('[data-connection="3"]').focus()
    page.keyboard.press('Enter')
    expect(page).to_have_url(BASE+'/tubing/#tubing=3')
    dimensions=[]
    for slug,selector,step in [('wiring','.joint-paper','[data-step="2"]'),('tubing','.joint-paper','[data-step="2"]')]:
        go(slug+'/');ready()
        expect(page.locator('.ag-steps')).to_be_visible()
        dimensions.append(page.locator('.ag-board-canvas').bounding_box())
        width=page.locator(selector).bounding_box()['width']
        page.locator('[data-action=zoom-in]').click()
        assert page.locator(selector).bounding_box()['width']>width
        page.locator('[data-action=zoom-fit]').click()
        # Wheel scrolling is not trapped by the diagram.
        page.evaluate('scrollTo(0,0)');page.locator('.ag-board-canvas').hover()
        before=page.evaluate('scrollY');page.mouse.wheel(0,350)
        page.wait_for_function('(before)=>scrollY>before',arg=before)
        page.evaluate('scrollTo(0,0)')
        page.locator('[data-action=fullscreen]').click()
        expect(page.locator('.ag-guide')).to_have_class(re.compile('ag-expanded'))
        page.wait_for_timeout(300)
        assert page.locator(selector).bounding_box()['width']>=width-1,slug+': fullscreen shows a smaller diagram'
        # the step renders on hashchange: until then ready() still sees the old canvas (BuildGuide#9)
        page.locator('.ag-steps').locator(step).click()
        expect(page.locator('.ag-steps').locator(step)).to_have_attribute('aria-current','step');ready()
        assert page.evaluate("document.fullscreenElement.classList.contains('ag-guide')")
        nav=page.locator('.ag-wire-navigation').bounding_box()
        assert nav['y']+nav['height']<=page.evaluate('innerHeight')+1
        page.locator('[data-action=fullscreen]').click()
        page.wait_for_function('!document.fullscreenElement')
    assert dimensions[0]['width']==dimensions[1]['width']
    go('bom/')
    expect(page.locator('thead th')).to_have_text(['Qty','Component','Specification'])
    expect(page.locator('tbody tr:not(.ag-group)')).to_have_count(len(bom))
    # Each BOM line has a tick, stored in this browser; it survives a reload and a search.
    expect(page.locator('tbody input[type=checkbox]')).to_have_count(len(bom))
    page.locator('tbody input[type=checkbox]').first.check()
    page.reload(wait_until='domcontentloaded')
    expect(page.locator('tbody input[type=checkbox]').first).to_be_checked()
    expect(page.locator('.ag-progress')).to_have_text(f"1 / {len(bom)} checked")
    page.locator('[data-role=search]').fill('Wago')
    page.locator('tbody input[type=checkbox]').first.check()
    expect(page.locator('.ag-progress')).to_have_text(f"2 / {len(bom)} checked")
    page.locator('[data-role=search]').fill('')
    # a click anywhere in a row ticks it
    page.locator('tbody tr:not(.ag-group)').nth(2).locator('td').nth(2).click()
    expect(page.locator('.ag-progress')).to_have_text(f"3 / {len(bom)} checked")
    expect(page.locator('tbody tr:not(.ag-group)').nth(2).locator('input[type=checkbox]')).to_be_checked()
    assert all('status' not in row for row in bom)
    page.locator('[data-role=search]').fill('Wago')
    expect(page.locator('tbody tr:not(.ag-group)')).to_have_count(3)
    with page.expect_download() as download:
        page.locator('[data-action=export]').click()
    with tempfile.TemporaryDirectory() as temp:
        target=Path(temp)/'bom.csv';download.value.save_as(target)
        rows=list(csv.DictReader(io.StringIO(target.read_text(encoding='utf-8-sig'))))
        assert list(rows[0])==['Group','Component','Specification','Quantity','MakerWorld']
        assert [r['Quantity'] for r in rows]==['3','1','2']
        assert download.value.suggested_filename=='autolever-bom.csv'
    page.locator('[data-role=search]').fill('does-not-exist')
    expect(page.locator('.ag-empty')).to_be_visible()
    page.locator('[data-role=search]').fill('')
    expect(page.locator('tbody tr:not(.ag-group)')).to_have_count(len(bom))
    # Printed parts are grouped, marked as 3D printed and link to MakerWorld.
    page.locator('[data-role=search]').fill('3D printed')
    expect(page.locator('tr.ag-group')).to_have_text(['3D printed'])
    expect(page.locator('tbody a', has_text='MakerWorld')).to_have_count(sum('link' in row for row in bom))
    page.locator('[data-role=search]').fill('')
    page.set_viewport_size({'width':390,'height':844})
    for path in ['', 'bom/', 'wiring/', 'tubing/']:
        go(path)
        assert page.evaluate('document.body.scrollWidth<=innerWidth'),path
        if path=='bom/':   # every specification on screen, not hidden in a sideways scroller
            assert page.evaluate("[...document.querySelectorAll('tbody tr:not(.ag-group) td:nth-child(3)')].every(td=>{const r=td.getBoundingClientRect();return r.width>0&&r.left>=0&&r.right<=innerWidth})"),'BOM specification off screen'
    # The next action stays on screen across step lengths and viewport changes.
    for width,height in [(1440,900),(1280,720),(390,844),(375,667),(844,390)]:
        page.set_viewport_size({'width':width,'height':height})
        for slug in ['wiring','tubing']:
            go(slug+'/');ready()
            steps=page.locator('.ag-steps button')
            for index in range(steps.count()):
                steps.nth(index).click()
                expect(steps.nth(index)).to_have_attribute('aria-current','step');ready()
                # the component takes the window height from its own top: scroll it to the top of the window
                page.evaluate("document.querySelector('.ag-guide').scrollIntoView()")
                page.wait_for_function('''() => {
                    const nav=document.querySelector('.ag-wire-navigation').getBoundingClientRect();
                    return nav.top>=0 && nav.bottom<=innerHeight;
                }''')
            page.locator('.ag-wire-navigation .ag-primary').scroll_into_view_if_needed()
    # The board stays readable on laptop screens.
    page.set_viewport_size({'width':1024,'height':768})
    go('wiring/#wiring=A/1');ready()
    assert page.locator('.ag-board-canvas').evaluate('e=>e.clientHeight')>=300,'board too small at 1024x768'
    assert not errors,errors
    assert not missing,missing
    assert not external,sorted(set(external))
    blocked=browser.new_context()
    blocked.route('**/*',lambda r:r.continue_() if r.request.url.startswith(BASE) else r.abort())
    blocked.add_init_script("Object.defineProperty(window,'localStorage',{get(){throw Error('blocked')}})")
    fallback=blocked.new_page();fallback.goto(BASE+'/wiring/',wait_until='domcontentloaded')
    expect(fallback.locator('.ag-status')).to_contain_text('Storage unavailable')
    fallback.locator('.ag-verify input').check()
    expect(fallback.locator('.ag-verify input')).to_be_checked()
    nojs=browser.new_context(java_script_enabled=False)
    fallback=nojs.new_page();fallback.goto(BASE+'/wiring/',wait_until='domcontentloaded')
    assert 'This guide needs JavaScript.' in fallback.content()
    browser.close()
    wires=[w for s in wiring for w in s['connections']]
    print(f"PASS: four Markdown pages with BuildGuide components; {len(wires)} connections ({sum(w['color']=='DIODE' for w in wires)} diodes), {len(tubing)} tubing steps, grouped BOM with 3D printed parts, safety admonition on every page (full on introduction and BOM, short with link on wiring and tubing); matching layouts, zoom, fullscreen, scrolling, persistence, CSV and mobile; no JS errors, missing assets or third-party requests.")
