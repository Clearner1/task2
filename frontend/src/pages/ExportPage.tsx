import { useExport, ExportPanel } from '@domains/review_export';
import { useToast } from '@foundation/providers/ToastProvider';
import './pages.css';

export function ExportPage() {
  const { batches, loading, triggerExport } = useExport();
  const { addToast } = useToast();

  const handleExportJson = async () => {
    const batch = await triggerExport(['json']);
    if (batch) {
      addToast('success', `Exported batch ${batch.batch_id} as JSON`);
    }
  };

  const handleExportJsonl = async () => {
    const batch = await triggerExport(['jsonl']);
    if (batch) {
      addToast('success', `Exported batch ${batch.batch_id} as JSONL`);
    }
  };

  return (
    <div className="animate-fade-in">
      <div className="page-header">
        <h2>Export</h2>
        <p>Export reviewed annotations to JSON or JSONL format</p>
      </div>

      <ExportPanel
        batches={batches}
        loading={loading}
        onExportJson={handleExportJson}
        onExportJsonl={handleExportJsonl}
      />
    </div>
  );
}
