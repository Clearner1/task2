import { useEffect } from 'react';
import { useMediaList, MediaList, ImportPanel } from '@domains/media';
import { usePagination } from '@foundation/hooks/use-pagination';
import { useToast } from '@foundation/providers/ToastProvider';
import './pages.css';

export function MediaPage() {
  const { data, loading, error, fetch, importMedia, preprocessMedia } = useMediaList();
  const { page, pageSize, setPage } = usePagination();
  const { addToast } = useToast();

  useEffect(() => {
    fetch({ page, page_size: pageSize });
  }, [fetch, page, pageSize]);

  useEffect(() => {
    if (error) addToast('error', error);
  }, [error, addToast]);

  const handleImport = async () => {
    const result = await importMedia();
    if (result) {
      addToast('success', `Imported ${result.imported} media files (${result.existing} existing)`);
      fetch({ page, page_size: pageSize });
    }
  };

  const handlePreprocess = async () => {
    const result = await preprocessMedia();
    if (result) {
      addToast('success', `Preprocessed ${result.processed} files (${result.failed} failed)`);
      fetch({ page, page_size: pageSize });
    }
  };

  return (
    <div className="animate-fade-in">
      <div className="page-header">
        <h2>Media</h2>
        <p>Import, preprocess, and manage audio/video files</p>
      </div>

      <ImportPanel
        loading={loading}
        mediaCount={data?.total ?? 0}
        onImport={handleImport}
        onPreprocess={handlePreprocess}
      />

      <div style={{ marginTop: 'var(--space-lg)' }}>
        <MediaList data={data} loading={loading} page={page} onPageChange={setPage} />
      </div>
    </div>
  );
}
