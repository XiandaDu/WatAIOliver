import { useState, useRef, useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { Button } from "@/components/ui/button"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { CourseSelector } from "@/components/ui/course-selector"
import { DragDropZone } from "@/components/ui/drag-drop-zone"
import AdminSidebar from "@/components/AdminSidebar"

// No mock data. All data is fetched from live APIs.

export default function AdminPage() {
  const fileInputRef = useRef(null)
  const navigate = useNavigate()
  const [selectedCourseId, setSelectedCourseId] = useState("")
  const [courses, setCourses] = useState([])
  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(false)
  const [showMetadataDialog, setShowMetadataDialog] = useState(false)
  const [pendingFiles, setPendingFiles] = useState([])
  const [fileMetadata, setFileMetadata] = useState([])
  const [isUploading, setIsUploading] = useState(false)
  const token = localStorage.getItem('access_token')

  // Load courses for selector
  useEffect(() => {
    const loadCourses = async () => {
      const resp = await fetch('http://localhost:8000/course/', {
        headers: { Authorization: `Bearer ${token}`}
      })
      if (resp.ok) {
        const data = await resp.json()
        setCourses(data)
      }
    }
    loadCourses()
  }, [])

  // Load documents for selected course
  useEffect(() => {
    const loadDocs = async () => {
      if (!selectedCourseId) { setDocuments([]); return }
      const resp = await fetch(`http://localhost:8000/documents?course_id=${encodeURIComponent(selectedCourseId)}`)
      if (resp.ok) {
        const data = await resp.json()
        setDocuments(data)
      }
    }
    loadDocs()
  }, [selectedCourseId])

  const handleUpdate = (row) => {
    // Navigate to edit page with row data
    navigate('/admin/edit', { state: { entry: row } })
  }

  const handleUpload = (id) => {
    console.log("Upload clicked for id:", id)
    fileInputRef.current.click()
    console.log(`Upload clicked for id: ${id}`)
  }

  const handleDelete = async (documentId) => {
    if (!selectedCourseId || !documentId) return
    
    // Delete from both metadata table and knowledge base
    const [metadataResp, kbResp] = await Promise.all([
      fetch(`http://localhost:8000/documents/${encodeURIComponent(documentId)}`, { method: 'DELETE' }),
      fetch(`http://localhost:8000/documents/kb?course_id=${encodeURIComponent(selectedCourseId)}&document_id=${encodeURIComponent(documentId)}`, { method: 'DELETE' })
    ])
    
    if (metadataResp.ok) {
      setDocuments(prev => prev.filter(doc => doc.document_id !== documentId))
    }
  }

  const handleRemoveDocs = (id) => {
    console.log(`Remove Docs clicked for id: ${id}`)
  }

  const handleExportLog = () => {
    if (!selectedCourseId) return
    navigate(`/admin/logs?course_id=${encodeURIComponent(selectedCourseId)}`);
  }

  const handleQandA = () => {
    if (!selectedCourseId) return
    navigate(`/chat?course_id=${encodeURIComponent(selectedCourseId)}`)
  }

  const handleFileChange = (event) => {
    const file = event.target.files[0]
    if (file) {
      console.log("Selected file:", file.name)
      throw new Error('File upload not implemented - API endpoint required');
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('user');
    localStorage.removeItem('access_token');
    navigate('/login');
  };

  const handleFilesDrop = async (files) => {
    if (!selectedCourseId) {
      alert('Please select a course first')
      return
    }

    // Prepare metadata for each file with defaults
    const metadata = files.map(file => ({
      file: file,
      title: file.name,
      term: ''
    }))

    setPendingFiles(files)
    setFileMetadata(metadata)
    setShowMetadataDialog(true)
  }

  const handleMetadataSubmit = async () => {
    if (isUploading) return; // Prevent multiple uploads
    
    setIsUploading(true)
    try {
      const uploadFormData = new FormData()
      uploadFormData.append('course_id', selectedCourseId)
      uploadFormData.append('user_id', 'admin')
      
      for (const item of fileMetadata) {
        uploadFormData.append('files', item.file)
      }
      
      const uploadResponse = await fetch('http://localhost:8000/chat/upload_files_for_rag', {
        method: 'POST',
        body: uploadFormData,
        signal: AbortSignal.timeout(300000)
      })
      
      if (uploadResponse.ok) {
        const uploadData = await uploadResponse.json()
        console.log('RAG upload completed successfully:', uploadData)
        
        // Update document metadata with custom titles and terms
        for (let i = 0; i < uploadData.results.length; i++) {
          const result = uploadData.results[i]
          const metadata = fileMetadata[i]
          if (result.status === 'completed' && result.rag_processing?.document_id) {
            // Update the document metadata with custom title and term
            await fetch(`http://localhost:8000/documents/${result.rag_processing.document_id}`, {
              method: 'PUT',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                title: metadata.title,
                term: metadata.term || null
              })
            })
          }
        }
        
        const successCount = uploadData.results.filter(r => r.status === 'completed').length
        const failedCount = uploadData.results.filter(r => r.status === 'failed').length
        
        if (failedCount > 0) {
          const failedFiles = uploadData.results.filter(r => r.status === 'failed')
          const errorMessages = failedFiles.map(f => `${f.filename}: ${f.error || 'Unknown error'}`).join('\n')
          alert(`Upload completed with issues:\n✅ ${successCount} files successful\n❌ ${failedCount} files failed:\n\n${errorMessages}`)
        } else {
          alert(`✅ Successfully uploaded ${successCount} files to RAG`)
        }
        
        // Close dialog and reset state
        setShowMetadataDialog(false)
        setPendingFiles([])
        setFileMetadata([])
        
        // Reload documents to show updated metadata
        if (selectedCourseId) {
          const resp = await fetch(`http://localhost:8000/documents?course_id=${encodeURIComponent(selectedCourseId)}`)
          if (resp.ok) {
            const data = await resp.json()
            setDocuments(data)
          }
        }
      } else {
        console.error('RAG upload failed:', uploadResponse.status, uploadResponse.statusText)
        alert('Upload failed')
      }
    } catch (error) {
      console.error("Error uploading files to RAG:", error)
      alert('Upload error')
    } finally {
      setIsUploading(false)
    }
  }

  const updateFileMetadata = (index, field, value) => {
    setFileMetadata(prev => prev.map((item, i) => 
      i === index ? { ...item, [field]: value } : item
    ))
  }

  return (
    <div className="flex h-screen bg-gray-50">
      <AdminSidebar title="Admin Panel" />
      <div className="flex-1 flex flex-col">
        <header className="flex items-center justify-between border-b border-gray-200 bg-white px-6 py-4">
          <h1 className="text-2xl font-semibold text-gray-900">Admin Panel</h1>
          <div>
            <Button>Add</Button>
            <Button
              variant="outline"
              className="ml-4"
              onClick={handleLogout}
            >
              Logout
            </Button>
          </div>
        </header>
        <main className="flex-1 overflow-y-auto p-6">
          <div className="mb-6 bg-white rounded-lg border p-6 space-y-4">
            <h2 className="text-lg font-semibold">Upload Files to RAG System</h2>
            <CourseSelector
              value={selectedCourseId}
              onChange={setSelectedCourseId}
              options={courses.map(c => ({ value: c.course_id, label: c.title }))}
            />
            {selectedCourseId && (
              <div className="flex space-x-4 mb-4">
                <Button variant="outline" onClick={handleExportLog}>
                  View Course Activity
                </Button>
                <Button variant="outline" onClick={handleQandA}>
                  Q and A for Course
                </Button>
              </div>
            )}
            <DragDropZone
              onFilesDrop={handleFilesDrop}
              acceptedFileTypes={["pdf", "doc", "docx", "txt", "tex", "md", "json", "csv"]}
              multiple={true}
            />
          </div>

          <div className="rounded-lg border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[50px]">#</TableHead>
                  <TableHead>Title</TableHead>
                  <TableHead>Term</TableHead>
                  <TableHead>Document ID</TableHead>
                  <TableHead>Operate</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {documents.map((doc, idx) => (
                  <TableRow key={doc.document_id}>
                    <TableCell>{idx + 1}</TableCell>
                    <TableCell className="font-medium">{doc.title}</TableCell>
                    <TableCell>{doc.term || '-'}</TableCell>
                    <TableCell className="max-w-xs truncate text-xs text-gray-500">{doc.document_id}</TableCell>
                    <TableCell>
                      <Button variant="destructive" size="sm" onClick={() => handleDelete(doc.document_id)}>Delete</Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </main>
      </div>

      {/* Metadata Input Dialog */}
      <Dialog open={showMetadataDialog} onOpenChange={setShowMetadataDialog}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>File Metadata</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <p className="text-sm text-gray-600">
              Please review and customize the metadata for each file. Press Enter or leave blank to use defaults.
            </p>
            {fileMetadata.map((item, index) => (
              <div key={index} className="border rounded-lg p-4 space-y-3">
                <h4 className="font-medium text-sm">File: {item.file.name}</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor={`title-${index}`}>Title</Label>
                    <Input
                      id={`title-${index}`}
                      value={item.title}
                      onChange={(e) => updateFileMetadata(index, 'title', e.target.value)}
                      placeholder={`Default: ${item.file.name}`}
                    />
                  </div>
                  <div>
                    <Label htmlFor={`term-${index}`}>Term (optional)</Label>
                    <Input
                      id={`term-${index}`}
                      value={item.term}
                      onChange={(e) => updateFileMetadata(index, 'term', e.target.value)}
                      placeholder="e.g., Fall 2024, Winter 2025"
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
          <DialogFooter>
            <Button 
              variant="outline" 
              onClick={() => setShowMetadataDialog(false)}
              disabled={isUploading}
            >
              Cancel
            </Button>
            <Button 
              onClick={handleMetadataSubmit}
              disabled={isUploading}
            >
              {isUploading ? 'Uploading...' : 'Upload Files'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        style={{ display: "none" }}
      />
    </div>
  )
} 