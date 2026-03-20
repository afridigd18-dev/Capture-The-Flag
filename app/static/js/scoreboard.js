/**
 * app/static/js/scoreboard.js — Live scoreboard AJAX polling every 30s.
 * Smoothly updates the leaderboard table without full page reload.
 */
(function () {
    const INTERVAL = 30000; // 30 seconds
    let countdown = 30;

    function updateCountdown() {
        const el = document.getElementById('countdown');
        if (el) el.textContent = countdown;
        countdown--;
        if (countdown < 0) {
            countdown = 30;
            fetchScoreboard();
        }
    }

    function fetchScoreboard() {
        fetch('/scoreboard/api', { credentials: 'same-origin' })
            .then(r => r.json())
            .then(data => {
                const tbody = document.getElementById('scoreboard-body');
                if (!tbody || !Array.isArray(data)) return;

                const currentUser = document.querySelector('meta[name="username"]')?.content || '';

                tbody.innerHTML = data.length === 0
                    ? '<tr><td colspan="5" class="text-center text-gray-600 py-10">No scores yet — go solve challenges!</td></tr>'
                    : data.map(entry => {
                        const rankDisplay = entry.rank === 1 ? '🥇' : entry.rank === 2 ? '🥈' : entry.rank === 3 ? '🥉' : `#${entry.rank}`;
                        const rankClass = entry.rank === 1 ? 'rank-1 text-lg' : entry.rank === 2 ? 'rank-2' : entry.rank === 3 ? 'rank-3' : 'text-gray-600';
                        const isMe = entry.username === currentUser;
                        return `<tr class="transition-colors ${isMe ? 'bg-green-900 bg-opacity-10 border-l-2 border-matrix' : ''}">
                <td class="font-bold ${rankClass}">${rankDisplay}</td>
                <td><a href="/profile/${entry.username}" class="hover:text-matrix transition-colors text-neon-cyan text-sm font-bold">${entry.username}</a>${isMe ? '<span class="text-xs text-gray-600 ml-2">← you</span>' : ''}</td>
                <td class="text-right text-neon-yellow font-bold">${entry.score}</td>
                <td class="text-right hidden sm:table-cell text-gray-500 text-sm">${entry.solve_count}</td>
                <td class="text-right hidden md:table-cell text-gray-700 text-xs">${entry.first_solve ? entry.first_solve.replace('T', ' ').slice(0, 16) : '—'}</td>
              </tr>`;
                    }).join('');

                // Update timestamp
                const ts = document.getElementById('last-update');
                if (ts) ts.textContent = 'Updated: ' + new Date().toLocaleTimeString();
            })
            .catch(() => { }); // Silently ignore network errors
    }

    // Inject current username for highlighting
    const usernameEl = document.querySelector('[data-username]');
    if (usernameEl) {
        const meta = document.createElement('meta');
        meta.name = 'username';
        meta.content = usernameEl.dataset.username;
        document.head.appendChild(meta);
    }

    setInterval(updateCountdown, 1000);
})();
