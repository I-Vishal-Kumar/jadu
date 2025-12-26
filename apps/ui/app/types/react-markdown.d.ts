// Type augmentation for react-markdown to work with React 19
import { ReactElement } from 'react';

declare module 'react-markdown' {
    import { ComponentPropsWithoutRef } from 'react';

    interface ReactMarkdownProps {
        children: string;
        remarkPlugins?: any[];
        rehypePlugins?: any[];
        components?: Record<string, any>;
        className?: string;
    }

    export default function ReactMarkdown(props: ReactMarkdownProps): ReactElement;
}
