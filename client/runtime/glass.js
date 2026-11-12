/* DSH 外观：全透明 + 不透明度滑块（毛玻璃模式在本机 Windows 上系统不支持，已移除） */
(function () {
	'use strict';
	try {
		if (window.__dshGlassUI) return;
		window.__dshGlassUI = true;

		var KEY = 'dsh.glass.v5';
		var DEFAULT_ALPHA = 0.12;
		var alpha = DEFAULT_ALPHA;
		try {
			var raw = localStorage.getItem(KEY);
			if (raw) {
				var p = JSON.parse(raw);
				if (p && typeof p.alpha === 'number' && p.alpha >= 0 && p.alpha <= 1) alpha = p.alpha;
			}
		} catch (e) { /* ignore */ }

		function applyAlpha() {
			try { document.documentElement.style.setProperty('--dsh-glass-alpha', String(alpha)); } catch (e) {}
		}
		applyAlpha();
		// 主进程据此把窗口背景设为透明（不使用系统材质）
		window.__dshGlassMode = 'clear';
		window.__dshGlassAlpha = alpha;

		var host = document.createElement('div');
		host.id = 'dsh-glass-host';
		host.style.cssText = 'position:fixed;right:0;bottom:0;width:0;height:0;z-index:2147483600;pointer-events:none;';
		var shadow = host.attachShadow({ mode: 'open' });

		var style = document.createElement('style');
		style.textContent = [
			':host{all:initial}',
			'*{box-sizing:border-box;font-family:"Segoe UI","Microsoft YaHei",system-ui,sans-serif;-webkit-user-select:none;user-select:none}',
			'.wrap{position:fixed;right:14px;bottom:14px;display:flex;flex-direction:column;align-items:flex-end;gap:10px;pointer-events:none}',
			'.btn{pointer-events:auto;-webkit-app-region:no-drag;width:32px;height:32px;border-radius:50%;border:1px solid rgba(0,0,0,.14);',
			'background:rgba(255,255,255,.94);color:#1b1b1c;display:flex;align-items:center;justify-content:center;cursor:pointer;',
			'box-shadow:0 3px 12px rgba(0,0,0,.2);opacity:.8;transition:transform .15s ease,opacity .15s ease}',
			'.btn:hover{transform:scale(1.07);opacity:1}',
			'.panel{pointer-events:auto;-webkit-app-region:no-drag;width:236px;padding:13px 14px 11px;border-radius:13px;',
			'background:rgba(255,255,255,.97);border:1px solid rgba(0,0,0,.1);box-shadow:0 16px 36px rgba(0,0,0,.25);',
			'color:#1b1b1c;display:none}',
			'.panel[data-open="1"]{display:block}',
			'.title{font-size:13px;font-weight:600;display:flex;align-items:center;justify-content:space-between;margin-bottom:4px}',
			'.title small{font-weight:400;font-size:11px;color:#6b7076}',
			'.row{display:flex;align-items:center;justify-content:space-between;font-size:12px;color:#3a3d42;margin:8px 0 0}',
			'.row b{font-weight:600;font-variant-numeric:tabular-nums;color:#111}',
			'input[type=range]{-webkit-appearance:none;appearance:none;width:100%;height:4px;border-radius:2px;outline:none;margin:9px 0 4px;',
			'background:linear-gradient(90deg,#3b82f6 var(--fill,15%),rgba(0,0,0,.14) var(--fill,15%))}',
			'input[type=range]::-webkit-slider-thumb{-webkit-appearance:none;appearance:none;width:14px;height:14px;border-radius:50%;background:#fff;',
			'border:1px solid rgba(0,0,0,.2);box-shadow:0 1px 4px rgba(0,0,0,.3);cursor:pointer}',
			'.hint{font-size:11px;line-height:1.5;color:#6b7076;margin-top:6px}',
			'.foot{display:flex;align-items:center;justify-content:space-between;margin-top:9px;padding-top:8px;border-top:1px solid rgba(0,0,0,.08)}',
			'.link{font-size:11px;color:#6b7076;cursor:pointer;background:none;border:none;padding:2px 0;text-decoration:underline;text-underline-offset:2px}',
			'.link:hover{color:#111}',
			'.dot{width:6px;height:6px;border-radius:50%;background:#3b82f6;display:inline-block;margin-right:6px;vertical-align:1px}',
		].join('\n');

		var wrap = document.createElement('div');
		wrap.className = 'wrap';
		var panel = document.createElement('div');
		panel.className = 'panel';

		var title = document.createElement('div');
		title.className = 'title';
		title.innerHTML = '<span><span class="dot"></span>外观</span><small>背景透明度</small>';

		var row = document.createElement('div');
		row.className = 'row';
		row.innerHTML = '<span>不透明度</span><b></b>';
		var range = document.createElement('input');
		range.type = 'range';
		range.min = '0';
		range.max = '100';
		range.step = '1';

		var hint = document.createElement('div');
		hint.className = 'hint';
		hint.textContent = '往左越透（能看到桌面，文字自动加深）；拉到最右就是客户端原样。'

		var foot = document.createElement('div');
		foot.className = 'foot';
		var reset = document.createElement('button');
		reset.className = 'link';
		reset.textContent = '恢复默认';
		var note = document.createElement('span');
		note.className = 'hint';
		note.style.margin = '0';
		note.textContent = 'Ctrl+Alt+G';
		foot.appendChild(reset);
		foot.appendChild(note);

		panel.appendChild(title);
		panel.appendChild(row);
		panel.appendChild(range);
		panel.appendChild(hint);
		panel.appendChild(foot);

		var btn = document.createElement('div');
		btn.className = 'btn';
		btn.title = '外观（Ctrl+Alt+G）';
		btn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3c3.5 4.2 6 7.6 6 10.5A6 6 0 0 1 6 13.5C6 10.6 8.5 7.2 12 3Z"/><path d="M9.5 14.2c.6 1.4 1.7 2.2 3 2.4"/></svg>';

		wrap.appendChild(panel);
		wrap.appendChild(btn);
		shadow.appendChild(style);
		shadow.appendChild(wrap);

		function sync() {
			var t = Math.round(alpha * 100);
			range.value = String(t);
			range.style.setProperty('--fill', t + '%');
			row.querySelector('b').textContent = t >= 100 ? '原样' : ('透明 ' + (100 - t) + '%');
			applyAlpha();
			window.__dshGlassMode = 'clear';
			window.__dshGlassAlpha = alpha;
			window.__dshGlassSolid = t >= 100;
		}
		function save() {
			try { localStorage.setItem(KEY, JSON.stringify({ alpha: alpha })); } catch (e) { /* ignore */ }
		}

		var open = false;
		function setOpen(next) { open = next; panel.dataset.open = next ? '1' : '0'; btn.style.opacity = next ? '1' : '.8'; }

		btn.addEventListener('click', function (e) { e.preventDefault(); e.stopPropagation(); setOpen(!open); });
		range.addEventListener('input', function () {
			var t = Number(range.value);
			if (!isFinite(t)) return;
			alpha = Math.min(1, Math.max(0, t / 100));
			applyAlpha();
			window.__dshGlassAlpha = alpha;
			window.__dshGlassSolid = t >= 100;
			range.style.setProperty('--fill', t + '%');
			row.querySelector('b').textContent = t >= 100 ? '原样' : ('透明 ' + (100 - t) + '%');
		});
		range.addEventListener('change', save);
		reset.addEventListener('click', function (e) {
			e.preventDefault();
			alpha = DEFAULT_ALPHA;
			sync();
			save();
		});
		document.addEventListener('keydown', function (e) {
			if (e.ctrlKey && e.altKey && (e.key === 'g' || e.key === 'G')) { e.preventDefault(); setOpen(!open); }
		}, true);

		sync();

		function mount() {
			if (!document.body || document.body.contains(host)) return;
			document.body.appendChild(host);
		}
		if (document.body) mount();
		else document.addEventListener('DOMContentLoaded', mount, { once: true });
	} catch (e) {
		try { console.warn('dsh glass panel failed', e); } catch (_) { /* ignore */ }
	}
})();

/* 自绘窗口按钮（最小化 / 最大化 / 关闭）：通过 document.title 给主进程发信号 */
(function () {
	'use strict';
	try {
		var hasBar = !!document.querySelector('.dsh-glass-winbar');
		window.__dshWinBtns = true;
		if (!hasBar) { /* 首次注入时继续创建 */ }
		// 样式自带一份，不依赖主进程注入的 glass.css（滑到"原样"时 CSS 会被撤掉）
		if (!document.getElementById('dsh-glass-winbtn-style')) {
			var st = document.createElement('style');
			st.id = 'dsh-glass-winbtn-style';
			st.textContent = [
				'#dsh-glass-dragstrip{position:fixed;top:0;left:210px;right:150px;height:40px;z-index:2147483001;-webkit-app-region:drag;}',
				'.dsh-glass-winbar{position:fixed;top:6px;right:8px;height:28px;display:flex;align-items:center;gap:2px;z-index:2147483002;-webkit-app-region:no-drag;}',
				'.dsh-glass-winbtn{width:38px;height:28px;border-radius:9px;display:flex;align-items:center;justify-content:center;cursor:default;color:var(--dsw-alias-label-secondary,#61666b);background:transparent;transition:background .12s ease,color .12s ease;}',
				'.dsh-glass-winbtn:hover{background:rgba(0,0,0,.09);}',
				'.dsh-glass-winbtn.dsh-close:hover{background:#e81123;color:#fff;}'
			].join('');
			(document.head || document.documentElement).appendChild(st);
		}
		if (hasBar) return;
		function send(action) {
			try {
				var old = document.title;
				document.title = 'DSHGLASS:' + action + ':' + Date.now();
				setTimeout(function () { try { document.title = old; } catch (e) {} }, 0);
			} catch (e) {}
		}
		var bar = document.createElement('div');
		bar.className = 'dsh-glass-winbar';
		var strip = document.createElement('div');
		strip.id = 'dsh-glass-dragstrip';
		var glyphs = {
			min: '<svg width="12" height="12" viewBox="0 0 12 12"><path d="M2 6h8" stroke="currentColor" stroke-width="1.2" fill="none"/></svg>',
			max: '<svg width="12" height="12" viewBox="0 0 12 12"><rect x="2.5" y="2.5" width="7" height="7" rx="1.4" stroke="currentColor" stroke-width="1.1" fill="none"/></svg>',
			close: '<svg width="12" height="12" viewBox="0 0 12 12"><path d="M3 3l6 6M9 3l-6 6" stroke="currentColor" stroke-width="1.2" fill="none"/></svg>'
		};
		['min', 'max', 'close'].forEach(function (k) {
			var b = document.createElement('div');
			b.className = 'dsh-glass-winbtn' + (k === 'close' ? ' dsh-close' : '');
			b.title = k === 'min' ? '最小化' : k === 'max' ? '最大化' : '关闭';
			b.innerHTML = glyphs[k];
			b.addEventListener('click', function (e) { e.preventDefault(); e.stopPropagation(); send(k); });
			bar.appendChild(b);
		});
		function mount() {
			if (!document.body) return;
			if (!document.getElementById('dsh-glass-winbtn-style')) {
				var st2 = document.getElementById('dsh-glass-winbtn-style');
				if (!st2) {
					var st3 = document.createElement('style');
					st3.id = 'dsh-glass-winbtn-style';
					st3.textContent = [
						'#dsh-glass-dragstrip{position:fixed;top:0;left:210px;right:150px;height:40px;z-index:2147483001;-webkit-app-region:drag;}',
						'.dsh-glass-winbar{position:fixed;top:6px;right:8px;height:28px;display:flex;align-items:center;gap:2px;z-index:2147483002;-webkit-app-region:no-drag;}',
						'.dsh-glass-winbtn{width:38px;height:28px;border-radius:9px;display:flex;align-items:center;justify-content:center;cursor:default;color:var(--dsw-alias-label-secondary,#61666b);background:transparent;transition:background .12s ease,color .12s ease;}',
						'.dsh-glass-winbtn:hover{background:rgba(0,0,0,.09);}',
						'.dsh-glass-winbtn.dsh-close:hover{background:#e81123;color:#fff;}'
					].join('');
					(document.head || document.documentElement).appendChild(st3);
				}
			}
			if (!document.getElementById('dsh-glass-dragstrip')) document.body.appendChild(strip);
			if (!document.querySelector('.dsh-glass-winbar')) document.body.appendChild(bar);
		}
		if (document.body) mount(); else document.addEventListener('DOMContentLoaded', mount, { once: true });
	} catch (e) {}
})();
