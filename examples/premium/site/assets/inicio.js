/* Roda antes de pintar a página: aplica o tema escolhido e liga as animações de entrada. */
(function () {
  var r = document.documentElement;
  r.classList.add('js');
  try { var t = localStorage.getItem('alto-lume-tema'); if (t === 'light' || t === 'dark') r.setAttribute('data-theme', t); } catch (e) {}
})();
