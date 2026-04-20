interface PaginationProps {
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
}

export function Pagination({ page, pageSize, total, onPageChange }: PaginationProps) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  const pages: number[] = [];
  const range = 2;
  for (let i = Math.max(1, page - range); i <= Math.min(totalPages, page + range); i++) {
    pages.push(i);
  }

  return (
    <nav className="ui-pagination" aria-label="Pagination">
      <button
        className="ui-pagination__btn"
        disabled={page <= 1}
        onClick={() => onPageChange(page - 1)}
        aria-label="Previous page"
      >
        ‹
      </button>

      {pages[0] > 1 && (
        <>
          <button className="ui-pagination__btn" onClick={() => onPageChange(1)}>1</button>
          {pages[0] > 2 && <span className="ui-pagination__info">…</span>}
        </>
      )}

      {pages.map((p) => (
        <button
          key={p}
          className={`ui-pagination__btn ${p === page ? 'ui-pagination__btn--active' : ''}`}
          onClick={() => onPageChange(p)}
          aria-current={p === page ? 'page' : undefined}
        >
          {p}
        </button>
      ))}

      {pages[pages.length - 1] < totalPages && (
        <>
          {pages[pages.length - 1] < totalPages - 1 && <span className="ui-pagination__info">…</span>}
          <button className="ui-pagination__btn" onClick={() => onPageChange(totalPages)}>
            {totalPages}
          </button>
        </>
      )}

      <button
        className="ui-pagination__btn"
        disabled={page >= totalPages}
        onClick={() => onPageChange(page + 1)}
        aria-label="Next page"
      >
        ›
      </button>

      <span className="ui-pagination__info">
        {total} items
      </span>
    </nav>
  );
}
