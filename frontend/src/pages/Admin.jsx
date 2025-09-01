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
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { DragDropZone } from "@/components/ui/drag-drop-zone"
import AdminSidebar from "@/components/AdminSidebar"

// No mock data. All data is fetched from live APIs.

export default function AdminPage() {
  const navigate = useNavigate()
  const [courses, setCourses] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedCourse, setSelectedCourse] = useState(null)
  const [editingCourse, setEditingCourse] = useState(null)
  const [showUploadDialog, setShowUploadDialog] = useState(false)
  const [showEditDialog, setShowEditDialog] = useState(false)
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [showMetadataDialog, setShowMetadataDialog] = useState(false)
  const [showDocumentsDialog, setShowDocumentsDialog] = useState(false)
  const [documentsDialogCourse, setDocumentsDialogCourse] = useState(null)
  const [documentsLoaded, setDocumentsLoaded] = useState(false)
  const [showCustomModelDialog, setShowCustomModelDialog] = useState(false)
  const [selectedCourseForModel, setSelectedCourseForModel] = useState(null)
  const [customModelData, setCustomModelData] = useState({
    name: '',
    api_key: '',
    model_type: 'openai'
  })
  const didFetchCourses = useRef(false)
  const [newCourse, setNewCourse] = useState({
    title: '',
    description: '',
    term: '',
    prompt: ''
  })
  const [pendingFiles, setPendingFiles] = useState([])
  const [fileMetadata, setFileMetadata] = useState([])
  const [isUploading, setIsUploading] = useState(false)
  const token = localStorage.getItem('access_token')

  useEffect(() => {
    // Guard against double invocation in React StrictMode (development)
    if (didFetchCourses.current) return
    didFetchCourses.current = true
    loadInstructorCourses()
  }, [])

  const loadInstructorCourses = async () => {
    try {
      setLoading(true)
      const response = await fetch('http://localhost:8000/course/my-courses', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      if (response.ok) {
        const coursesData = await response.json()
        // Preserve already loaded documents if present to avoid flicker
        setCourses(prev =>
          coursesData.map(course => {
            const existing = prev.find(c => c.course_id === course.course_id)
            return existing && existing.documents
              ? { ...course, documents: existing.documents }
              : course
          })
        )
      } else {
        setError('Failed to load courses')
      }
    } catch (error) {
      console.error('Error loading courses:', error)
      setError('Error loading courses')
    } finally {
      setLoading(false)
    }
  }

  // Load documents for selected course
  const loadDocuments = async (courseId) => {
    if (!courseId) return []
    try {
      const resp = await fetch(`http://localhost:8000/documents/?course_id=${encodeURIComponent(courseId)}`)
      if (resp.ok) {
        const documents = await resp.json()
        console.log(`Loaded ${documents.length} documents for course ${courseId}`)
        return documents
      } else {
        console.error(`Failed to load documents for course ${courseId}:`, resp.status, resp.statusText)
      }
    } catch (error) {
      console.error('Error loading documents:', error)
    }
    return []
  }

  const handleUpdate = (course) => {
    setEditingCourse({ ...course })
    setShowEditDialog(true)
  }

  const handleUpload = (course) => {
    setSelectedCourse(course)
    setShowUploadDialog(true)
  }

  const handleDeleteCourse = async (courseId) => {
    if (!confirm('Are you sure you want to delete this course? This action cannot be undone.')) {
      return
    }
    
    try {
      const resp = await fetch(`http://localhost:8000/course/${courseId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      })
      
      if (resp.ok) {
        setCourses(prev => prev.filter(course => course.course_id !== courseId))
      } else {
        alert('Failed to delete course')
      }
    } catch (error) {
      console.error('Error deleting course:', error)
      alert('Error deleting course')
    }
  }

  const handleDeleteDocument = async (documentId, courseId) => {
    if (!courseId || !documentId) return
    
    try {
      // Delete from both metadata table and knowledge base
      const [metadataResp, kbResp] = await Promise.all([
        fetch(`http://localhost:8000/documents/${encodeURIComponent(documentId)}`, { method: 'DELETE' }),
        fetch(`http://localhost:8000/documents/kb?course_id=${encodeURIComponent(courseId)}&document_id=${encodeURIComponent(documentId)}`, { method: 'DELETE' })
      ])
      
      if (metadataResp.ok) {
        // Reload course data to update document list
        const updatedCourses = await Promise.all(
          courses.map(async (course) => {
            if (course.course_id === courseId) {
              const docs = await loadDocuments(courseId)
              return { ...course, documents: docs }
            }
            return course
          })
        )
        setCourses(updatedCourses)
      }
    } catch (error) {
      console.error('Error deleting document:', error)
    }
  }

  const handleViewActivity = (course) => {
    navigate(`/admin/logs?course_id=${encodeURIComponent(course.course_id)}`);
  }

  const handleQandA = (course) => {
    navigate(`/chat?course_id=${encodeURIComponent(course.course_id)}`)
  }

  const handleOpenAIAPI = (course) => {
    setSelectedCourseForModel(course)
    setCustomModelData({
      name: '',
      api_key: '',
      model_type: 'openai'
    })
    setShowCustomModelDialog(true)
  }

  const handleCustomModelSubmit = async () => {
    if (!selectedCourseForModel || !customModelData.name.trim() || !customModelData.api_key.trim()) {
      alert('Please fill in all required fields')
      return
    }

    try {
      const response = await fetch(`http://localhost:8000/course/${selectedCourseForModel.course_id}/custom-models`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(customModelData)
      })

      if (response.ok) {
        alert(`Custom model "${customModelData.name}" added successfully!`)
        setShowCustomModelDialog(false)
        setCustomModelData({
          name: '',
          api_key: '',
          model_type: 'openai'
        })
        setSelectedCourseForModel(null)
      } else {
        const errorData = await response.json()
        alert(`Failed to add custom model: ${errorData.detail || 'Unknown error'}`)
      }
    } catch (error) {
      console.error('Error adding custom model:', error)
      alert('Error adding custom model')
    }
  }

  const handleSaveCourse = async () => {
    if (!editingCourse) return
    
    try {
      const resp = await fetch(`http://localhost:8000/course/${editingCourse.course_id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          title: editingCourse.title,
          description: editingCourse.description,
          term: editingCourse.term,
          prompt: editingCourse.prompt
        })
      })
      
      if (resp.ok) {
        const updatedCourse = await resp.json()
        // Merge existing documents to avoid losing them after update
        setCourses(prev => prev.map(course =>
          course.course_id === updatedCourse.course_id
            ? { ...updatedCourse, documents: course.documents }
            : course
        ))
        setShowEditDialog(false)
        setEditingCourse(null)
      } else {
        alert('Failed to update course')
      }
    } catch (error) {
      console.error('Error updating course:', error)
      alert('Error updating course')
    }
  }

  const handleCreateCourse = async () => {
    if (!newCourse.title.trim()) {
      alert('Course title is required')
      return
    }
    
    try {
      const resp = await fetch('http://localhost:8000/course/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(newCourse)
      })
      
      if (resp.ok) {
        const createdCourse = await resp.json()
        setCourses(prev => [...prev, { ...createdCourse, documents: [] }])
        setShowCreateDialog(false)
        setNewCourse({
          title: '',
          description: '',
          term: '',
          prompt: ''
        })
      } else {
        alert('Failed to create course')
      }
    } catch (error) {
      console.error('Error creating course:', error)
      alert('Error creating course')
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('user');
    localStorage.removeItem('access_token');
    navigate('/login');
  };

  // Load documents for each course automatically
  useEffect(() => {
    const loadAllDocuments = async () => {
      if (documentsLoaded) return // Prevent duplicate loading
      
      console.log(`Auto-loading documents for ${courses.length} courses...`)
      const coursesWithDocs = await Promise.all(
        courses.map(async (course) => {
          const docs = await loadDocuments(course.course_id)
          console.log(`Course ${course.title} (${course.course_id}): ${docs.length} documents`)
          return { ...course, documents: docs }
        })
      )
      setCourses(coursesWithDocs)
      setDocumentsLoaded(true)
      console.log('Auto-load completed:', coursesWithDocs.map(c => 
        `${c.title}: ${c.documents?.length || 0} docs`
      ).join(', '))
    }
    
    // Load documents when we have courses and haven't loaded documents yet
    if (courses.length > 0 && !documentsLoaded) {
      loadAllDocuments()
    }
  }, [courses, documentsLoaded])

  const handleFilesDrop = async (files) => {
    if (!selectedCourse) {
      alert('No course selected')
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
    setShowUploadDialog(false)
    setShowMetadataDialog(true)
  }

  const handleMetadataSubmit = async () => {
    if (isUploading) return; // Prevent multiple uploads
    
    setIsUploading(true)
    try {
      const uploadFormData = new FormData()
      uploadFormData.append('course_id', selectedCourse.course_id)
      uploadFormData.append('user_id', 'admin')
      
      for (const item of fileMetadata) {
        uploadFormData.append('files', item.file)
      }
      
      const uploadResponse = await fetch('http://localhost:8000/chat/upload_files_for_rag', {
        method: 'POST',
        body: uploadFormData,
        signal: AbortSignal.timeout(1200000) // 20 minutes to match backend
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
          alert(`Upload completed with issues:\n${successCount} files successful\n${failedCount} files failed:\n\n${errorMessages}`)
        } else {
          alert(`Successfully uploaded ${successCount} files to RAG`)
        }
        
        // Close dialog and reset state
        setShowMetadataDialog(false)
        setPendingFiles([])
        setFileMetadata([])
        
        // Reload documents to show updated metadata
        if (selectedCourse) {
          const updatedCourses = await Promise.all(
            courses.map(async (course) => {
              if (course.course_id === selectedCourse.course_id) {
                const docs = await loadDocuments(course.course_id)
                return { ...course, documents: docs }
              }
              return course
            })
          )
          setCourses(updatedCourses)
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
            <Button onClick={() => setShowCreateDialog(true)}>Add Course</Button>
            <Button
              variant="outline"
              className="ml-4 text-red-600 border-red-300 hover:bg-red-50 hover:text-red-700"
              onClick={handleLogout}
            >
              Logout
            </Button>
          </div>
        </header>
        <main className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                <p className="text-gray-600">Loading courses...</p>
              </div>
            </div>
          ) : error ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-center">
                <div className="text-red-600 text-xl mb-2">️</div>
                <p className="text-red-600 mb-4">{error}</p>
                <Button onClick={loadInstructorCourses} variant="outline">
                  Try Again
                </Button>
              </div>
            </div>
          ) : courses.length === 0 ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-center">
                <div className="text-gray-400 text-xl mb-2"></div>
                <p className="text-gray-600 mb-4">No courses found</p>
                <Button onClick={() => setShowCreateDialog(true)}>
                  Create Your First Course
                </Button>
              </div>
            </div>
          ) : (
            <div className="rounded-lg border bg-white">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[50px]">#</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead>Notes</TableHead>
                    <TableHead>Invite Code</TableHead>
                    <TableHead>Doc</TableHead>
                    <TableHead>Prompt</TableHead>
                    <TableHead>Operate</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {courses.map((course, idx) => (
                    <TableRow key={`${course.course_id}-${course.documents?.length || 0}`}>
                      <TableCell>{idx + 1}</TableCell>
                      <TableCell className="font-medium">{course.title}</TableCell>
                      <TableCell className="max-w-xs">
                        <div className="truncate">{course.description || '-'}</div>
                        {course.term && <div className="text-sm text-gray-500">Term: {course.term}</div>}
                      </TableCell>
                      <TableCell className="min-w-[120px]">
                        {course.invite_code ? (
                          <div className="text-center">
                            <div className="flex items-center justify-center space-x-2">
                              <div className="font-mono text-lg font-bold bg-blue-100 text-blue-800 px-3 py-2 rounded-lg border-2 border-blue-300">
                                {course.invite_code}
                              </div>
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-8 w-8 p-0 text-blue-600 hover:text-blue-800"
                                onClick={(event) => {
                                  navigator.clipboard.writeText(course.invite_code);
                                  // Show brief feedback
                                  const btn = event.target;
                                  const originalText = btn.innerHTML;
                                  btn.innerHTML = '✓';
                                  btn.className = 'h-8 w-8 p-0 text-green-600';
                                  setTimeout(() => {
                                    btn.innerHTML = originalText;
                                    btn.className = 'h-8 w-8 p-0 text-blue-600 hover:text-blue-800';
                                  }, 1000);
                                }}
                                title="Copy invite code"
                              >
                                📋
                              </Button>
                            </div>
                            <div className="text-xs text-gray-500 mt-1">Share with students</div>
                          </div>
                        ) : (
                          <span className="text-gray-400 text-sm">No code</span>
                        )}
                      </TableCell>
                      <TableCell className="min-w-[250px]">
                        {course.documents && course.documents.length > 0 ? (
                          <div className="space-y-1">
                            {course.documents.slice(0, 3).map((doc) => (
                              <div key={doc.document_id} className="flex items-center justify-between text-sm bg-gray-50 p-2 rounded border">
                                <div className="flex-1 min-w-0">
                                  <div className="font-medium truncate">{doc.title || 'Untitled Document'}</div>
                                  {doc.term ? (
                                    <div className="text-xs text-blue-600 bg-blue-50 px-1 rounded mt-1 inline-block">
                                      {doc.term}
                                    </div>
                                  ) : (
                                    <div className="text-xs text-gray-400 mt-1">
                                      No term specified
                                    </div>
                                  )}
                                  <div className="text-xs text-gray-500 mt-1">
                                    ID: {doc.document_id.slice(0, 8)}...
                                  </div>
                                </div>
                                <Button 
                                  variant="ghost" 
                                  size="sm" 
                                  className="h-6 w-6 p-0 text-red-500 hover:text-red-700 ml-2 flex-shrink-0"
                                  onClick={() => handleDeleteDocument(doc.document_id, course.course_id)}
                                >
                                  ×
                                </Button>
                              </div>
                            ))}
                            {course.documents.length > 3 && (
                              <Button 
                                variant="ghost" 
                                size="sm" 
                                className="text-xs text-blue-600 hover:text-blue-800 w-full"
                                onClick={() => {
                                  setDocumentsDialogCourse(course)
                                  setShowDocumentsDialog(true)
                                }}
                              >
                                View all {course.documents.length} documents
                              </Button>
                            )}
                          </div>
                        ) : (
                          <span className="text-gray-400">No documents</span>
                        )}
                      </TableCell>
                      <TableCell className="max-w-xs">
                        <div className="truncate text-sm">{course.prompt || 'Default prompt'}</div>
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-col space-y-1">
                          <Button variant="outline" size="sm" onClick={() => handleUpdate(course)}>
                            Update
                          </Button>
                          <Button variant="destructive" size="sm" onClick={() => handleDeleteCourse(course.course_id)}>
                            Delete
                          </Button>
                          <Button variant="outline" size="sm" onClick={() => handleUpload(course)}>
                            Upload
                          </Button>
                          <Button variant="ghost" size="sm" onClick={() => handleViewActivity(course)}>
                            View Log
                          </Button>
                          <Button variant="ghost" size="sm" onClick={() => handleQandA(course)}>
                            Q and A
                          </Button>
                          <Button variant="ghost" size="sm" onClick={() => handleOpenAIAPI(course)}>
                            OpenAI API
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </main>
      </div>

      {/* Upload Dialog */}
      <Dialog open={showUploadDialog} onOpenChange={setShowUploadDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Upload Files to {selectedCourse?.title}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <DragDropZone
              onFilesDrop={handleFilesDrop}
              acceptedFileTypes={["pdf", "doc", "docx", "txt", "tex", "md", "json", "csv"]}
              multiple={true}
            />
          </div>
        </DialogContent>
      </Dialog>

      {/* Edit Course Dialog */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Edit Course</DialogTitle>
          </DialogHeader>
          {editingCourse && (
            <div className="space-y-4">
              <div>
                <Label htmlFor="course-title">Course Name</Label>
                <Input
                  id="course-title"
                  value={editingCourse.title}
                  onChange={(e) => setEditingCourse(prev => ({ ...prev, title: e.target.value }))}
                />
              </div>
              <div>
                <Label htmlFor="course-description">Description</Label>
                <Textarea
                  id="course-description"
                  value={editingCourse.description || ''}
                  onChange={(e) => setEditingCourse(prev => ({ ...prev, description: e.target.value }))}
                />
              </div>
              <div>
                <Label htmlFor="course-term">Term</Label>
                <Input
                  id="course-term"
                  value={editingCourse.term || ''}
                  onChange={(e) => setEditingCourse(prev => ({ ...prev, term: e.target.value }))}
                  placeholder="e.g., Fall 2024"
                />
              </div>

              <div>
                <Label htmlFor="course-prompt">Custom Prompt</Label>
                <Textarea
                  id="course-prompt"
                  value={editingCourse.prompt || ''}
                  onChange={(e) => setEditingCourse(prev => ({ ...prev, prompt: e.target.value }))}
                  placeholder="Enter custom system prompt for this course..."
                  rows={4}
                />
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowEditDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleSaveCourse}>
              Save Changes
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Create Course Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Create New Course</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="new-course-title">Course Name *</Label>
              <Input
                id="new-course-title"
                value={newCourse.title}
                onChange={(e) => setNewCourse(prev => ({ ...prev, title: e.target.value }))}
                placeholder="Enter course name"
              />
            </div>
            <div>
              <Label htmlFor="new-course-description">Description</Label>
              <Textarea
                id="new-course-description"
                value={newCourse.description}
                onChange={(e) => setNewCourse(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Enter course description"
              />
            </div>
            <div>
              <Label htmlFor="new-course-term">Term</Label>
              <Input
                id="new-course-term"
                value={newCourse.term}
                onChange={(e) => setNewCourse(prev => ({ ...prev, term: e.target.value }))}
                placeholder="e.g., Fall 2024"
              />
            </div>

            <div>
              <Label htmlFor="new-course-prompt">Custom Prompt</Label>
              <Textarea
                id="new-course-prompt"
                value={newCourse.prompt}
                onChange={(e) => setNewCourse(prev => ({ ...prev, prompt: e.target.value }))}
                placeholder="Enter custom system prompt for this course..."
                rows={4}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateCourse}>
              Create Course
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Metadata Input Dialog */}
      <Dialog 
        open={showMetadataDialog} 
        onOpenChange={(open) => {
          if (!open && isUploading) {
            // Prevent closing during upload with confirmation
            const confirmed = confirm(
              "Upload in progress! Closing this window may interrupt the upload process. Are you sure you want to close?"
            )
            if (confirmed) {
              setShowMetadataDialog(false)
              setIsUploading(false) // Reset upload state
            }
          } else if (!isUploading) {
            setShowMetadataDialog(open)
          }
        }}
      >
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>File Metadata</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <p className="text-sm text-gray-600">
              Please review and customize the metadata for each file. Press Enter or leave blank to use defaults.
            </p>
            {isUploading && (
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
                <p className="text-sm text-amber-800 font-medium">
                  ⚠️ Upload in progress - Do not close this window!
                </p>
                <p className="text-xs text-amber-700 mt-1">
                  Closing this window may interrupt the upload process.
                </p>
              </div>
            )}
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

      {/* View All Documents Dialog */}
      <Dialog open={showDocumentsDialog} onOpenChange={setShowDocumentsDialog}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              Documents for {documentsDialogCourse?.title}
              {documentsDialogCourse?.term && ` (${documentsDialogCourse.term})`}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            {documentsDialogCourse?.documents?.map((doc) => (
              <div key={doc.document_id} className="border rounded-lg p-4 bg-gray-50">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <h4 className="font-medium text-lg mb-2">{doc.title || 'Untitled Document'}</h4>
                    <div className="grid grid-cols-2 gap-4 text-sm text-gray-600 mb-3">
                      <div>
                        <span className="font-medium">Document ID:</span>
                        <div className="font-mono text-xs bg-white px-2 py-1 rounded mt-1">
                          {doc.document_id}
                        </div>
                      </div>
                      <div>
                        <span className="font-medium">Term:</span>
                        <div className="mt-1">
                          {doc.term ? (
                            <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">
                              {doc.term}
                            </span>
                          ) : (
                            <span className="bg-gray-100 text-gray-600 px-2 py-1 rounded text-xs">
                              No term specified
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    {doc.created_at && (
                      <div className="text-xs text-gray-500">
                        Created: {new Date(doc.created_at).toLocaleString()}
                      </div>
                    )}
                    {doc.updated_at && doc.updated_at !== doc.created_at && (
                      <div className="text-xs text-gray-500">
                        Updated: {new Date(doc.updated_at).toLocaleString()}
                      </div>
                    )}
                  </div>
                  <Button 
                    variant="destructive" 
                    size="sm"
                    className="ml-4"
                    onClick={() => {
                      handleDeleteDocument(doc.document_id, documentsDialogCourse.course_id)
                      setShowDocumentsDialog(false)
                    }}
                  >
                    Delete
                  </Button>
                </div>
              </div>
            )) || (
              <div className="text-center text-gray-500 py-8">
                No documents found for this course.
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDocumentsDialog(false)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Custom Model Dialog */}
      <Dialog open={showCustomModelDialog} onOpenChange={setShowCustomModelDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Add Custom OpenAI Model</DialogTitle>
          </DialogHeader>
          {selectedCourseForModel && (
            <div className="space-y-4">
              <div className="text-sm text-gray-600">
                Adding custom model for: <strong>{selectedCourseForModel.title}</strong>
              </div>
              <div>
                <Label htmlFor="model-name">Model Name *</Label>
                <Input
                  id="model-name"
                  value={customModelData.name}
                  onChange={(e) => setCustomModelData(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="e.g., ChatGPT-5, Custom GPT-4"
                />
              </div>
              <div>
                <Label htmlFor="api-key">OpenAI API Key *</Label>
                <Input
                  id="api-key"
                  type="password"
                  value={customModelData.api_key}
                  onChange={(e) => setCustomModelData(prev => ({ ...prev, api_key: e.target.value }))}
                  placeholder="sk-..."
                />
              </div>
              <div>
                <Label htmlFor="model-type">Model Type</Label>
                <Select
                  value={customModelData.model_type}
                  onValueChange={(value) => setCustomModelData(prev => ({ ...prev, model_type: value }))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="openai">OpenAI</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCustomModelDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleCustomModelSubmit}>
              Add Model
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
} 