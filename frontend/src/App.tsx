import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import UploadPage from "./pages/UploadPage";
import ArchivePage from "./pages/ArchivePage";
import MeetingDetailPage from "./pages/MeetingDetailPage";
import AnalyticsPage from "./pages/AnalyticsPage";

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<UploadPage />} />
        <Route path="/archive" element={<ArchivePage />} />
        <Route path="/meetings/:id" element={<MeetingDetailPage />} />
        <Route path="/analytics" element={<AnalyticsPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
}
