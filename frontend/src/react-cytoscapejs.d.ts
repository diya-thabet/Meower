declare module 'react-cytoscapejs' {
  import type { ComponentType, CSSProperties } from 'react'
  import type { ElementsDefinition, LayoutOptions, Stylesheet } from 'cytoscape'

  interface CytoscapeComponentProps {
    elements: ElementsDefinition['nodes'] | ElementsDefinition['edges'] | Array<{ data: Record<string, unknown> }>
    layout?: LayoutOptions
    style?: CSSProperties
    stylesheet?: Stylesheet | Stylesheet[]
    className?: string
    cy?: (cy: import('cytoscape').Core) => void
  }

  const CytoscapeComponent: ComponentType<CytoscapeComponentProps>
  export default CytoscapeComponent
}
