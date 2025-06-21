import { useState, useRef } from "react"
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
import AdminSidebar from "@/components/AdminSidebar"

const data = [
  {
    id: 1,
    name: "test",
    notes: "",
    doc: "/uploads/Lions.txt,/uploads/Tigers.txt",
    model: "nemo",
    prompt:
      "You are an expert in the field, providing detailed and technical insights. Be thorough and offer advanced perspectives. {background}. {system_prompt}. The question you are answering is",
  },
  {
    id: 2,
    name: "CS251_test2",
    notes: "",
    doc: "/uploads/02-2-combinational-logic-zhk.tex,/uploads/02-3-transistors.tex,/uploads/02-4-components.tex,/uploads/02-intro-to-digital-logic-zhk.tex,/uploads/lec1-3.tex,/uploads/lec1-f24.tex,/uploads/lec2-1.tex,/uploads/lec2-2-1.tex,/uploads/lec3-1.tex,/uploads/lec3.tex,/uploads/lec4-1.tex,/uploads/lec4-2-copy.tex",
    model: "nemo",
    prompt:
      "You are a creative and adaptive virtual teaching assistant designed to quiz students and provide meaningful learning experiences. When quizzing a student on a topic, start with basic questions to assess their foundational knowledge. Gradually increase the difficulty based on their performance, moving from simple definitions to complex scenarios and application-level problems. After each response, evaluate the answer and provide detailed feedback: If the answer is correct, affirm their understanding and introduce a slightly more challenging follow-up question. If the answer is incorrect, gently correct their misunderstanding, provide a clear explanation, and ask a related but simpler question to reinforce the concept. Your goal is to create a supportive and effective learning environment that adapts to the student's needs. {background}. {system_prompt}. The question you are answering is",
  },
]

export default function AdminPage() {
  const fileInputRef = useRef(null)
  const navigate = useNavigate()

  const handleUpdate = (row) => {
    // Navigate to edit page with row data
    navigate('/admin/edit', { state: { entry: row } })
  }

  const handleUpload = (id) => {
    console.log("Upload clicked for id:", id)
    fileInputRef.current.click()
    console.log(`Upload clicked for id: ${id}`)
  }

  const handleDelete = (id) => {
    console.log(`Delete clicked for id: ${id}`)
  }

  const handleRemoveDocs = (id) => {
    console.log(`Remove Docs clicked for id: ${id}`)
  }

  const handleExportLog = (id) => {
    console.log(`Export Log clicked for id: ${id}`)
  }

  const handleQandA = (id) => {
    console.log(`Q and A clicked for id: ${id}`)
  }

  const handleFileChange = (event) => {
    const file = event.target.files[0]
    if (file) {
      console.log("Selected file:", file.name)
      // Placeholder for upload logic
    }
  }

  return (
    <div className="flex h-screen bg-gray-50">
      <AdminSidebar title="Admin Panel" />
      <div className="flex-1 flex flex-col">
        <header className="flex items-center justify-between border-b border-gray-200 bg-white px-6 py-4">
          <h1 className="text-2xl font-semibold text-gray-900">Admin Panel</h1>
          <div>
            <Button>Add</Button>
            <a href="#" className="ml-4 text-sm font-medium text-gray-600 hover:text-gray-900">
              Logout
            </a>
          </div>
        </header>
        <main className="flex-1 overflow-y-auto p-6">
          <div className="rounded-lg border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[50px]">#</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead>Notes</TableHead>
                  <TableHead>Doc</TableHead>
                  <TableHead>Model</TableHead>
                  <TableHead>Prompt</TableHead>
                  <TableHead>Operate</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.map((row) => (
                  <TableRow key={row.id}>
                    <TableCell>{row.id}</TableCell>
                    <TableCell className="font-medium">{row.name}</TableCell>
                    <TableCell>{row.notes}</TableCell>
                    <TableCell className="max-w-xs truncate text-xs text-gray-500">{row.doc}</TableCell>
                    <TableCell>{row.model}</TableCell>
                    <TableCell className="max-w-xs whitespace-normal text-xs">{row.prompt}</TableCell>
                    <TableCell>
                      <div className="flex flex-col space-y-2">
                        <Button variant="outline" size="sm" onClick={() => handleUpdate(row)}>Update</Button>
                        <Button variant="destructive" size="sm" onClick={() => handleDelete(row.id)}>Delete</Button>
                        <Button variant="outline" size="sm" onClick={() => handleUpload(row.id)}>Upload</Button>
                        <Button variant="outline" size="sm" onClick={() => handleRemoveDocs(row.id)}>Remove Docs</Button>
                        <Button variant="outline" size="sm" onClick={() => handleExportLog(row.id)}>Export Log</Button>
                        <Button variant="outline" size="sm" onClick={() => handleQandA(row.id)}>Q and A</Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </main>
      </div>

      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        style={{ display: "none" }}
      />
    </div>
  )
} 