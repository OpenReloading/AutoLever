import Link from '@docusaurus/Link'
import Heading from '@theme/Heading'
import type { ReactNode } from 'react'

/** The 404 page: one sentence with the two ways in. */
export default function NotFoundContent({ className }: { className?: string }): ReactNode {
  return (
    <main className={`container margin-vert--xl ${className ?? ''}`}>
      <Heading as="h1">Page not found</Heading>
      <p>
        That page does not exist, start from the <Link to="/">Introduction</Link> or the{' '}
        <Link to="/bom/">BOM</Link>.
      </p>
    </main>
  )
}
