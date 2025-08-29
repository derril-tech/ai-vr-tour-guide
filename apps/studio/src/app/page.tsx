import { Suspense } from 'react'
import { DashboardHeader } from '@/components/dashboard/header'
import { DashboardSidebar } from '@/components/dashboard/sidebar'
import { SitesList } from '@/components/sites/sites-list'
import { LoadingSpinner } from '@/components/ui/loading-spinner'

export default function DashboardPage() {
  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <DashboardSidebar />
      
      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <DashboardHeader />
        
        <main className="flex-1 overflow-y-auto p-6">
          <div className="max-w-7xl mx-auto">
            <div className="mb-8">
              <h1 className="text-3xl font-bold tracking-tight">Sites</h1>
              <p className="text-muted-foreground">
                Manage your VR tour sites and experiences
              </p>
            </div>
            
            <Suspense fallback={<LoadingSpinner />}>
              <SitesList />
            </Suspense>
          </div>
        </main>
      </div>
    </div>
  )
}
