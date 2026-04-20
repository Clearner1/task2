import { useAnnotationWorkbench, AnnotationWorkbench } from '@domains/annotation';
import { useToast } from '@foundation/providers/ToastProvider';
import './pages.css';

export function AnnotationPage() {
  const {
    task,
    annotation,
    loading,
    saving,
    dirty,
    error,
    fetchNext,
    heartbeat,
    autosave,
    skip,
    submit,
    updateAnnotation,
  } = useAnnotationWorkbench();
  const { addToast } = useToast();

  const handleSubmit = async () => {
    const success = await submit();
    if (success) {
      addToast('success', 'Annotation submitted successfully!');
      // Auto-fetch next task after successful submit
      setTimeout(() => fetchNext(), 600);
    } else {
      addToast('error', error || 'Submission failed');
    }
  };

  return (
    <div>
      <div className="page-header">
        <h2>Annotate</h2>
        <p>Listen to media and label emotional content</p>
      </div>

      <AnnotationWorkbench
        task={task}
        annotation={annotation}
        loading={loading}
        saving={saving}
        dirty={dirty}
        error={error}
        onFetchNext={fetchNext}
        onHeartbeat={heartbeat}
        onAutosave={autosave}
        onSkip={skip}
        onSubmit={handleSubmit}
        onUpdateAnnotation={updateAnnotation}
      />
    </div>
  );
}
