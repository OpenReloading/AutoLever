"""Browser checks for the dedicated guide pages. Requires Playwright + Chromium.
Run with MkDocs serving: python tests/check_guide.py [http://127.0.0.1:8000]
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
        expect(page.locator('#ag-content')).to_be_visible()
    def ready():
        expect(page.locator('.ag-board-canvas')).to_have_attribute('data-ready','true')
    go()
    data=json.loads(page.locator('#guide-data').text_content())
    expect(page.locator('.ag-nav a')).to_have_text(['Introduction','BOM','Wiring','Tubing'])
    # The safety warning sits above the content on every page, without exact figures.
    expect(page.locator('.ag-nav + .ag-warning + #ag-content')).to_have_count(1)
    expect(page.locator('.ag-warning')).to_contain_text('E-STOP is not a safety-rated')
    expect(page.locator('.ag-prerelease')).to_contain_text('Pre-release')
    expect(page.locator('.ag-warning')).to_contain_text('electricity')
    expect(page.locator('.ag-warning')).not_to_contain_text(re.compile(r'\d+ ?(N|bar)\b'))
    expect(page.locator('#assembly-guide h1')).to_have_text(data['intro']['title'])
    expect(page.locator('.ag-lead').first).to_contain_text('Lee APP')
    expect(page.locator('.ag-intro h2')).to_have_text([s['title'] for s in data['intro']['sections']])
    expect(page.locator('.ag-wordmark')).to_have_text('AutoLever')
    expect(page.locator('.ag-flow, .ag-intro-steps')).to_have_count(0)
    # Real page navigation, reload and browser back preserve the destination.
    for name,slug in [('BOM','bom'),('Wiring','wiring'),('Tubing','tubing')]:
        page.locator('.ag-nav').get_by_role('link',name=name,exact=True).click()
        expect(page).to_have_url(BASE+'/'+slug+'/')
        page.reload(wait_until='domcontentloaded')
        expect(page.locator('#assembly-guide h1')).to_have_text(name)
        expect(page.locator('.ag-warning')).to_be_visible()
    expect(page.locator('.ag-step-note')).to_have_count(0)
    page.go_back(wait_until='domcontentloaded')
    expect(page.locator('#assembly-guide h1')).to_have_text('Wiring')
    # Every board connection matches the validated source, with no extra diode wires.
    for step in data['steps']:
        for wire in step['wires']:
            go(f"wiring/#{step['id']}/{wire['no']}");ready()
            expect(page.locator('.ag-connection-detail')).to_contain_text(wire['la'])
            expect(page.locator('.ag-connection-detail')).to_contain_text(wire['lb'])
            expect(page.locator('[data-connection]')).to_have_count(len(step['wires']))
            expect(page.locator('[data-connection="'+wire['no']+'"]')).to_have_attribute('aria-label',wire['no']+': '+wire['la']+' to '+wire['lb']+('; ring at '+wire['la'] if wire['col']=='DIODE' else ''))
    go('wiring/#A/1');ready()
    page.locator('#ag-wire-scope').select_option('single');ready()
    expect(page.locator('[data-connection]')).to_have_count(1)
    page.locator('#ag-wire-scope').select_option('all');ready()
    expect(page.locator('[data-connection]')).to_have_count(sum(len(s['wires']) for s in data['steps']))
    page.locator('#ag-wire-scope').select_option('step');ready()
    page.locator('.ag-verify input').check()
    expect(page.locator('.ag-wire-row.selected input')).to_be_checked()
    page.reload(wait_until='domcontentloaded')
    expect(page.locator('.ag-verify input')).to_be_checked()
    page.locator('[data-action=next-wire]').click()
    expect(page.locator('.ag-wire-row.selected .ag-wire-number')).to_have_text('2')
    expect(page.locator('.ag-verify input')).not_to_be_checked()
    # A tick belongs to one exact connection: an old tick for wire 16 with other ends stays unchecked.
    page.evaluate("localStorage.setItem('autolever-guide',JSON.stringify({'wire-16:H1:-:X-M2:2':true}))")
    go('wiring/#C/16');ready()
    expect(page.locator('.ag-verify input')).not_to_be_checked()
    go('wiring/#A/1')
    page.locator('[data-action=prev-wire]').click()
    expect(page.locator('.ag-wire-row.selected .ag-wire-number')).to_have_text(data['steps'][0]['wires'][-1]['no'])
    go('wiring/#H/'+data['steps'][-1]['wires'][-1]['no'])
    page.locator('[data-action=next-wire]').click()
    expect(page).to_have_url(BASE+'/tubing/#1')
    # Tubing has the same workspace, zoom, scope, selection and fullscreen controls.
    for i,tube in enumerate(data['tubes']):
        go(f'tubing/#{i+1}');ready()
        expect(page.locator('.ag-connection-detail')).to_contain_text(tube['from'])
        expect(page.locator('.ag-connection-detail')).to_contain_text(tube['to'])
        expect(page.locator('[data-air-route]')).to_have_count(len(data['tubes']))   # tubing shows every connection by default
        page.locator('.ag-verify input').check()
    page.reload(wait_until='domcontentloaded')
    tubes=len(data['tubes'])
    expect(page.locator('.ag-progress')).to_have_text(f'{tubes} / {tubes} checked')
    expect(page.locator('[data-action=next-tube]')).to_be_disabled()
    page.locator('#ag-wire-scope').select_option('all');ready()
    expect(page.locator('[data-air-route]')).to_have_count(tubes)
    page.locator('[data-air-route="2"]').focus()
    page.keyboard.press('Enter')
    expect(page).to_have_url(BASE+'/tubing/#3')
    dimensions=[]
    for slug,selector,step in [('wiring','.joint-paper','[data-step="2"]'),('tubing','.ag-air-paper','[data-tube="2"]')]:
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
        expect(page.locator('#assembly-guide')).to_have_class(re.compile('ag-expanded'))
        page.wait_for_timeout(300)
        assert page.locator(selector).bounding_box()['width']>=width-1,slug+': fullscreen shows a smaller diagram'
        page.locator('.ag-steps').locator(step).click();ready()
        assert page.evaluate('document.fullscreenElement.id')=='assembly-guide'
        nav=page.locator('.ag-wire-navigation').bounding_box()
        assert nav['y']+nav['height']<=page.evaluate('innerHeight')+1
        page.locator('[data-action=fullscreen]').click()
        page.wait_for_function('!document.fullscreenElement')
    assert dimensions[0]['width']==dimensions[1]['width']
    go('bom/')
    expect(page.locator('thead th')).to_have_text(['Qty','Component','Specification'])
    expect(page.locator('tbody tr:not(.ag-group)')).to_have_count(len(data['bom']))
    expect(page.locator('#assembly-guide').locator('[data-filter], .ag-bom-stats')).to_have_count(0)
    # Each BOM line has a tick, stored in this browser; it survives a reload and a search.
    expect(page.locator('tbody input[type=checkbox]')).to_have_count(len(data['bom']))
    page.locator('tbody input[type=checkbox]').first.check()
    page.reload(wait_until='domcontentloaded')
    expect(page.locator('tbody input[type=checkbox]').first).to_be_checked()
    expect(page.locator('.ag-progress')).to_have_text(f"1 / {len(data['bom'])} checked")
    page.locator('#ag-search').fill('Wago')
    page.locator('tbody input[type=checkbox]').first.check()
    expect(page.locator('.ag-progress')).to_have_text(f"2 / {len(data['bom'])} checked")
    page.locator('#ag-search').fill('')
    # a click anywhere in a row ticks it
    page.locator('tbody tr:not(.ag-group)').nth(2).locator('td').nth(2).click()
    expect(page.locator('.ag-progress')).to_have_text(f"3 / {len(data['bom'])} checked")
    expect(page.locator('tbody tr:not(.ag-group)').nth(2).locator('input[type=checkbox]')).to_be_checked()
    assert all('status' not in row for row in data['bom'])
    page.locator('#ag-search').fill('Wago')
    expect(page.locator('tbody tr:not(.ag-group)')).to_have_count(3)
    with page.expect_download() as download:
        page.locator('[data-action=export]').click()
    with tempfile.TemporaryDirectory() as temp:
        target=Path(temp)/'bom.csv';download.value.save_as(target)
        rows=list(csv.DictReader(io.StringIO(target.read_text(encoding='utf-8-sig'))))
        assert list(rows[0])==['Group','Component','Specification','Quantity','MakerWorld']
        assert [r['Quantity'] for r in rows]==['3','1','2']
        assert download.value.suggested_filename=='autolever-bom.csv'
    page.locator('#ag-search').fill('does-not-exist')
    expect(page.locator('.ag-empty')).to_be_visible()
    page.locator('#ag-search').fill('')
    expect(page.locator('tbody tr:not(.ag-group)')).to_have_count(len(data['bom']))
    # Printed parts are grouped, marked as 3D printed and link to MakerWorld.
    page.locator('#ag-search').fill('3D printed')
    expect(page.locator('tr.ag-group')).to_have_text(['3D printed'])
    expect(page.locator('tbody a', has_text='MakerWorld')).to_have_count(sum('makerworld' in row for row in data['bom']))
    page.locator('#ag-search').fill('')
    # No links to removed pages or manufacturer lists.
    for path in ['', 'bom/', 'wiring/', 'tubing/']:
        go(path)
        for text in ['Manufacturer references', 'Original guide', 'Open wiring']:
            expect(page.get_by_text(text)).to_have_count(0)
    page.set_viewport_size({'width':390,'height':844})
    for path in ['', 'bom/', 'wiring/', 'tubing/']:
        go(path)
        assert page.evaluate('document.body.scrollWidth<=innerWidth'),path
        expect(page.locator('.ag-nav a')).to_have_text(['Introduction','BOM','Wiring','Tubing'])
        if path=='bom/':   # every specification on screen, not hidden in a sideways scroller
            assert page.evaluate("[...document.querySelectorAll('tbody tr:not(.ag-group) td:nth-child(3)')].every(td=>{const r=td.getBoundingClientRect();return r.width>0&&r.left>=0&&r.right<=innerWidth})"),'BOM specification off screen'
        expect(page.get_by_role('button',name='Connection detail',exact=True)).to_have_count(0)
    # The next action stays on screen across step lengths and viewport changes.
    for width,height in [(1440,900),(1280,720),(390,844),(375,667),(844,390)]:
        page.set_viewport_size({'width':width,'height':height})
        for slug in ['wiring','tubing']:
            go(slug+'/');ready()
            steps=page.locator('.ag-steps button')
            for index in range(steps.count()):
                steps.nth(index).click();ready()
                # short landscape screens: the safety warning scrolls away, the board keeps its minimum height
                page.evaluate("scrollTo(0,innerHeight<500?document.querySelector('.ag-warning').getBoundingClientRect().bottom+scrollY:0)")
                page.wait_for_function('''() => {
                    const nav=document.querySelector('.ag-wire-navigation').getBoundingClientRect();
                    return nav.top>=0 && nav.bottom<=innerHeight;
                }''')
            page.locator('.ag-wire-navigation .ag-primary').scroll_into_view_if_needed()
    # The board stays readable on laptop screens.
    page.set_viewport_size({'width':1024,'height':768})
    go('wiring/#A/1');ready()
    assert page.locator('.ag-board-canvas').evaluate('e=>e.clientHeight')>=300,'board too small at 1024x768'
    assert not errors,errors
    assert not missing,missing
    assert not external,sorted(set(external))
    blocked=browser.new_context()
    blocked.route('**/*',lambda r:r.continue_() if r.request.url.startswith(BASE) else r.abort())
    blocked.add_init_script("Object.defineProperty(window,'localStorage',{get(){throw Error('blocked')}})")
    fallback=blocked.new_page();fallback.goto(BASE+'/wiring/',wait_until='domcontentloaded')
    expect(fallback.locator('.ag-footer')).to_contain_text('Storage unavailable')
    fallback.locator('.ag-verify input').check()
    expect(fallback.locator('.ag-verify input')).to_be_checked()
    nojs=browser.new_context(java_script_enabled=False)
    fallback=nojs.new_page();fallback.goto(BASE+'/',wait_until='domcontentloaded')
    assert 'This guide needs JavaScript.' in fallback.content()
    browser.close()
    wires=[w for s in data['steps'] for w in s['wires']]
    print(f"PASS: four pages; {len(wires)} connections ({sum(w['col']=='DIODE' for w in wires)} diodes), {len(data['tubes'])} tubing steps, grouped BOM with 3D printed parts, safety warning on every page; matching layouts, zoom, fullscreen, scrolling, persistence, CSV and mobile; no JS errors, missing assets or third-party requests.")
