import { NavLink, Outlet } from 'react-router-dom';
import './pages.css';

const NAV_ITEMS = [
  { to: '/', icon: '◈', label: 'Dashboard' },
  { to: '/media', icon: '♫', label: 'Media' },
  { to: '/tasks', icon: '☰', label: 'Tasks' },
  { to: '/annotate', icon: '✎', label: 'Annotate' },
  { to: '/review', icon: '✓', label: 'Review' },
  { to: '/export', icon: '↗', label: 'Export' },
];

export function Layout() {
  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="sidebar__brand">
          <h1>Task2</h1>
          <p>Sentiment Annotation</p>
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
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
