'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Plus, MapPin, Calendar, MoreHorizontal } from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { CreateSiteDialog } from './create-site-dialog'

// Mock data - in real app this would come from API
const mockSites = [
  {
    id: '1',
    name: 'Ancient Rome Tour',
    description: 'Explore the Colosseum and Roman Forum in immersive VR',
    location: 'Rome, Italy',
    status: 'published',
    createdAt: '2024-01-15',
    toursCount: 3,
    hotspotsCount: 12,
  },
  {
    id: '2',
    name: 'Egyptian Pyramids',
    description: 'Journey through the Great Pyramid of Giza',
    location: 'Giza, Egypt',
    status: 'draft',
    createdAt: '2024-01-10',
    toursCount: 1,
    hotspotsCount: 8,
  },
  {
    id: '3',
    name: 'Machu Picchu Experience',
    description: 'Discover the lost city of the Incas',
    location: 'Cusco, Peru',
    status: 'published',
    createdAt: '2024-01-05',
    toursCount: 2,
    hotspotsCount: 15,
  },
]

export function SitesList() {
  const [showCreateDialog, setShowCreateDialog] = useState(false)

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'published':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300'
      case 'draft':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300'
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300'
    }
  }

  return (
    <div className="space-y-6">
      {/* Header Actions */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Your Sites</h2>
          <p className="text-muted-foreground">
            Create and manage VR tour sites
          </p>
        </div>
        <Button onClick={() => setShowCreateDialog(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Create Site
        </Button>
      </div>

      {/* Sites Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {mockSites.map((site) => (
          <Card key={site.id} className="hover:shadow-lg transition-shadow">
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <CardTitle className="text-lg">{site.name}</CardTitle>
                  <div className="flex items-center text-sm text-muted-foreground">
                    <MapPin className="mr-1 h-3 w-3" />
                    {site.location}
                  </div>
                </div>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="sm">
                      <MoreHorizontal className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem>Edit</DropdownMenuItem>
                    <DropdownMenuItem>Duplicate</DropdownMenuItem>
                    <DropdownMenuItem>Export</DropdownMenuItem>
                    <DropdownMenuItem className="text-destructive">
                      Delete
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <CardDescription className="line-clamp-2">
                {site.description}
              </CardDescription>
              
              <div className="flex items-center justify-between">
                <Badge className={getStatusColor(site.status)}>
                  {site.status}
                </Badge>
                <div className="flex items-center text-sm text-muted-foreground">
                  <Calendar className="mr-1 h-3 w-3" />
                  {new Date(site.createdAt).toLocaleDateString()}
                </div>
              </div>
              
              <div className="flex justify-between text-sm text-muted-foreground">
                <span>{site.toursCount} tours</span>
                <span>{site.hotspotsCount} hotspots</span>
              </div>
              
              <div className="flex gap-2 pt-2">
                <Button size="sm" className="flex-1">
                  Edit Site
                </Button>
                <Button size="sm" variant="outline" className="flex-1">
                  Preview
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Create Site Dialog */}
      <CreateSiteDialog
        open={showCreateDialog}
        onOpenChange={setShowCreateDialog}
      />
    </div>
  )
}
