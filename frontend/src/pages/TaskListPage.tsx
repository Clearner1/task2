import { useEffect, useState } from 'react';
import { useTaskList, TaskList } from '@domains/annotation';
import { usePagination } from '@foundation/hooks/use-pagination';
import './pages.css';

export function TaskListPage() {
  const { data, loading, fetch } = useTaskList();
  const { page, pageSize, setPage } = usePagination();
  const [statusFilter, setStatusFilter] = useState('');

  useEffect(() => {
    fetch({ page, page_size: pageSize, status: statusFilter || undefined });
  }, [fetch, page, pageSize, statusFilter]);

  const handleStatusChange = (status: string) => {
    setStatusFilter(status);
    setPage(1);
  };

  const handleSelectTask = (taskId: string) => {
    // Navigate to annotate page with task context (could use URL param)
    window.location.hash = `/annotate?task=${taskId}`;
  };

  return (
    <div className="animate-fade-in">
      <div className="page-header">
        <h2>Tasks</h2>
        <p>Browse and filter annotation tasks by status</p>
      </div>

      <TaskList
        data={data}
        loading={loading}
        page={page}
        statusFilter={statusFilter}
        onPageChange={setPage}
        onStatusFilterChange={handleStatusChange}
        onSelectTask={handleSelectTask}
      />
    </div>
  );
}
