import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ApiProvider } from '@foundation/providers/ApiProvider';
import { ToastProvider } from '@foundation/providers/ToastProvider';
import { createMockAdapter } from '@foundation/adapters/mock-adapter';
import { createRealAdapter } from '@foundation/adapters/real-adapter';
import { Layout } from '@pages/Layout';
import { DashboardPage } from '@pages/DashboardPage';
import { MediaPage } from '@pages/MediaPage';
import { TaskListPage } from '@pages/TaskListPage';
import { AnnotationPage } from '@pages/AnnotationPage';
import { ReviewPage } from '@pages/ReviewPage';
import { ExportPage } from '@pages/ExportPage';

// Use ?mock query param or VITE_USE_MOCK env to toggle
const useMock = new URLSearchParams(window.location.search).has('mock')
  || import.meta.env.VITE_USE_MOCK === 'true';

const adapter = useMock ? createMockAdapter() : createRealAdapter();

export default function App() {
  return (
    <ApiProvider adapter={adapter}>
      <ToastProvider>
        <BrowserRouter>
          <Routes>
            <Route element={<Layout />}>
              <Route index element={<DashboardPage />} />
              <Route path="media" element={<MediaPage />} />
              <Route path="tasks" element={<TaskListPage />} />
              <Route path="annotate" element={<AnnotationPage />} />
              <Route path="review" element={<ReviewPage />} />
              <Route path="export" element={<ExportPage />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </ToastProvider>
    </ApiProvider>
  );
}
