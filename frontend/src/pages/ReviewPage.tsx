import { useReview } from '@domains/review_export';
import { ReviewPanel } from '@domains/review_export';
import { useToast } from '@foundation/providers/ToastProvider';
import './pages.css';

export function ReviewPage() {
  const { submittedTasks, loading, fetchSubmitted, approve, reject } = useReview();
  const { addToast } = useToast();

  const handleApprove = async (taskId: string) => {
    const ok = await approve(taskId);
    if (ok) {
      addToast('success', `Task ${taskId} approved`);
      fetchSubmitted();
    }
  };

  const handleReject = async (taskId: string) => {
    const ok = await reject(taskId);
    if (ok) {
      addToast('info', `Task ${taskId} rejected`);
      fetchSubmitted();
    }
  };

  return (
    <div className="animate-fade-in">
      <div className="page-header">
        <h2>Review</h2>
        <p>Review submitted annotations before export</p>
      </div>

      <ReviewPanel
        data={submittedTasks}
        loading={loading}
        onFetch={fetchSubmitted}
        onApprove={handleApprove}
        onReject={handleReject}
      />
    </div>
  );
}
