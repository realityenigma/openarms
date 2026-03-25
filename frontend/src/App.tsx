import React from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import HomePage from './pages/HomePage'
import ModelPage from './pages/ModelPage'
import DatasetPage from './pages/DatasetPage'
import NewModelPage from './pages/NewModelPage'
import NewDatasetPage from './pages/NewDatasetPage'
import TopNav from './components/TopNav'

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <TopNav />
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/new-model" element={<NewModelPage />} />
        <Route path="/new-dataset" element={<NewDatasetPage />} />
        <Route path="/models/*" element={<ModelPage />} />
        <Route path="/datasets/*" element={<DatasetPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
