import { NavLink, Outlet } from 'react-router-dom';
import './pages.css';

const NAV_ITEMS = [
  { to: '/', icon: '◈', label: 'Dashboard', hint: 'System pulse' },
  { to: '/media', icon: '♫', label: 'Media', hint: 'Ingest and normalize' },
  { to: '/tasks', icon: '☰', label: 'Tasks', hint: 'Queue and filters' },
  { to: '/annotate', icon: '✎', label: 'Annotate', hint: 'Workbench' },
  { to: '/review', icon: '✓', label: 'Review', hint: 'Quality gate' },
  { to: '/export', icon: '↗', label: 'Export', hint: 'Release JSON' },
];

export function Layout() {
  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="sidebar__brand">
          <span className="sidebar__brand-kicker">Emotion Lab Console</span>
          <h1>Task2</h1>
          <p>Human-in-the-loop annotation workspace for normalized audio and video review.</p>
        </div>
        <nav className="sidebar__nav">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `sidebar__link ${isActive ? 'sidebar__link--active' : ''}`
              }
              id={`nav-${item.label.toLowerCase()}`}
            >
              <span className="sidebar__link-icon">{item.icon}</span>
              <span className="sidebar__link-copy">
                <span className="sidebar__link-label">{item.label}</span>
                <span className="sidebar__link-hint">{item.hint}</span>
              </span>
            </NavLink>
          ))}
        </nav>
        <div className="sidebar__footer">
          <span>24h-ready runtime</span>
          <span>Review before export</span>
        </div>
      </aside>
      <main className="main-content">
        <div className="content-shell">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
