/**
 * C.O.V.E.R.T - Main Application Component
 */

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AppLayout } from './components/layout/AppLayout';
import { ReporterDashboard } from './pages/ReporterDashboard';
import { SubmitReport } from './pages/SubmitReport';
import { MySubmissions } from './components/reporter/MySubmissions';

function App() {
  return (
    <BrowserRouter>
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#1f2937',
            color: '#f9fafb',
          },
        }}
      />
      <Routes>
        {/* Redirect root to dashboard */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />

        {/* Main app routes with layout */}
        <Route element={<AppLayout />}>
          <Route path="/dashboard" element={<ReporterDashboard />} />
          <Route path="/submit" element={<SubmitReport />} />
          <Route path="/my-reports" element={<MySubmissions />} />
        </Route>

        {/* 404 fallback */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
