import * as vscode from 'vscode';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

let searchResultsProvider: SearchResultsProvider;
let aiderContextProvider: AiderContextProvider;

export function activate(context: vscode.ExtensionContext) {
    console.log('Code Indexer + Aider extension activated');

    // Initialize providers
    searchResultsProvider = new SearchResultsProvider();
    aiderContextProvider = new AiderContextProvider();

    // Register tree data providers
    vscode.window.registerTreeDataProvider('searchResults', searchResultsProvider);
    vscode.window.registerTreeDataProvider('aiderContext', aiderContextProvider);

    // Register commands
    context.subscriptions.push(
        vscode.commands.registerCommand('codeIndexer.search', searchCode),
        vscode.commands.registerCommand('codeIndexer.indexAndOpenAider', indexAndOpenAider),
        vscode.commands.registerCommand('codeIndexer.refreshIndex', refreshIndex),
        vscode.commands.registerCommand('codeIndexer.addToAiderContext', addToAiderContext)
    );

    // Auto-index on workspace open
    const config = vscode.workspace.getConfiguration('codeIndexer');
    if (config.get('autoIndex')) {
        refreshIndex();
    }
}

async function searchCode() {
    const query = await vscode.window.showInputBox({
        prompt: 'Enter semantic search query',
        placeHolder: 'e.g., "function that validates email"'
    });

    if (!query) return;

    try {
        const config = vscode.workspace.getConfiguration('codeIndexer');
        const indexerPath = config.get('indexerPath') as string;
        
        const { stdout } = await execAsync(
            `python "${indexerPath}" search "${query}" --top-k 10`
        );

        // Parse results
        const results = parseSearchResults(stdout);
        searchResultsProvider.update(results);

        // Show results panel
        vscode.commands.executeCommand('workbench.view.extension.codeIndexer');

        vscode.window.showInformationMessage(`Found ${results.length} results`);
    } catch (error) {
        vscode.window.showErrorMessage(`Search failed: ${error}`);
    }
}

async function indexAndOpenAider() {
    // Step 1: Get task description
    const task = await vscode.window.showInputBox({
        prompt: 'Describe the coding task',
        placeHolder: 'e.g., "Add authentication to API endpoints"'
    });

    if (!task) return;

    // Step 2: Search for relevant context
    const searchQuery = await vscode.window.showInputBox({
        prompt: 'Search query for context (optional)',
        placeHolder: 'e.g., "authentication middleware"'
    });

    try {
        const config = vscode.workspace.getConfiguration('codeIndexer');
        const indexerPath = config.get('indexerPath') as string;
        const workspaceRoot = vscode.workspace.workspaceFolders?.[0].uri.fsPath;

        // Refresh index
        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "Indexing codebase...",
        }, async () => {
            await execAsync(`python "${indexerPath}" index "${workspaceRoot}"`);
        });

        // Search if query provided
        let filesToAdd: string[] = [];
        if (searchQuery) {
            const { stdout } = await execAsync(
                `python "${indexerPath}" search "${searchQuery}" --top-k 5`
            );
            filesToAdd = parseSearchResults(stdout).map(r => r.filePath);
        }

        // Generate map
        await execAsync(
            `python "${indexerPath}" map "${workspaceRoot}" --output .aider-context.txt`
        );

        // Build Aider command
        let aiderCmd = 'wsl aider --model azure/gpt-4o';
        
        if (filesToAdd.length > 0) {
            aiderCmd += ' ' + filesToAdd.map(f => `"${f}"`).join(' ');
        }
        
        aiderCmd += ' --read .aider-context.txt';
        aiderCmd += ` --message "${task}"`;

        // Open terminal and run Aider
        const terminal = vscode.window.createTerminal('Aider + Code Indexer');
        terminal.show();
        terminal.sendText(aiderCmd);

        vscode.window.showInformationMessage('🚀 Aider session started with indexed context!');
    } catch (error) {
        vscode.window.showErrorMessage(`Failed to start Aider: ${error}`);
    }
}

async function refreshIndex() {
    const config = vscode.workspace.getConfiguration('codeIndexer');
    const indexerPath = config.get('indexerPath') as string;
    const workspaceRoot = vscode.workspace.workspaceFolders?.[0].uri.fsPath;

    await vscode.window.withProgress({
        location: vscode.ProgressLocation.Notification,
        title: "Refreshing code index...",
    }, async () => {
        await execAsync(`python "${indexerPath}" index "${workspaceRoot}"`);
    });

    vscode.window.showInformationMessage('✅ Code index refreshed!');
}

async function addToAiderContext(item: SearchResultItem) {
    aiderContextProvider.addFile(item.filePath);
    vscode.window.showInformationMessage(`Added ${item.label} to Aider context`);
}

function parseSearchResults(output: string): SearchResult[] {
    const results: SearchResult[] = [];
    const lines = output.split('\n');
    
    let current: Partial<SearchResult> = {};
    
    for (const line of lines) {
        if (line.includes('(function)') || line.includes('(class)') || line.includes('(method)')) {
            if (current.name) {
                results.push(current as SearchResult);
            }
            const match = line.match(/(\d+)\.\s+(.+?)\s+\((.+?)\)\s+-\s+([\d.]+)/);
            if (match) {
                current = {
                    name: match[2],
                    type: match[3],
                    similarity: parseFloat(match[4])
                };
            }
        } else if (line.includes('📁')) {
            current.filePath = line.split('📁')[1].trim();
        } else if (line.includes('📝')) {
            current.signature = line.split('📝')[1].trim();
        }
    }
    
    if (current.name) {
        results.push(current as SearchResult);
    }
    
    return results;
}

// Tree view providers
class SearchResultsProvider implements vscode.TreeDataProvider<SearchResultItem> {
    private _onDidChangeTreeData = new vscode.EventEmitter<SearchResultItem | undefined>();
    readonly onDidChangeTreeData = this._onDidChangeTreeData.event;
    
    private results: SearchResult[] = [];

    update(results: SearchResult[]) {
        this.results = results;
        this._onDidChangeTreeData.fire(undefined);
    }

    getTreeItem(element: SearchResultItem): vscode.TreeItem {
        return element;
    }

    getChildren(element?: SearchResultItem): SearchResultItem[] {
        if (!element) {
            return this.results.map(r => new SearchResultItem(r));
        }
        return [];
    }
}

class AiderContextProvider implements vscode.TreeDataProvider<vscode.TreeItem> {
    private _onDidChangeTreeData = new vscode.EventEmitter<vscode.TreeItem | undefined>();
    readonly onDidChangeTreeData = this._onDidChangeTreeData.event;
    
    private files: string[] = [];

    addFile(filePath: string) {
        if (!this.files.includes(filePath)) {
            this.files.push(filePath);
            this._onDidChangeTreeData.fire(undefined);
        }
    }

    getTreeItem(element: vscode.TreeItem): vscode.TreeItem {
        return element;
    }

    getChildren(): vscode.TreeItem[] {
        return this.files.map(f => {
            const item = new vscode.TreeItem(f);
            item.command = {
                command: 'vscode.open',
                title: 'Open File',
                arguments: [vscode.Uri.file(f)]
            };
            return item;
        });
    }
}

class SearchResultItem extends vscode.TreeItem {
    constructor(public readonly result: SearchResult) {
        super(result.name, vscode.TreeItemCollapsibleState.None);
        
        this.description = `${result.type} - ${(result.similarity * 100).toFixed(0)}%`;
        this.tooltip = result.signature;
        this.iconPath = new vscode.ThemeIcon('symbol-' + result.type);
        
        this.command = {
            command: 'vscode.open',
            title: 'Open File',
            arguments: [vscode.Uri.file(result.filePath)]
        };
        
        this.contextValue = 'searchResult';
    }
    
    get filePath(): string {
        return this.result.filePath;
    }
}

interface SearchResult {
    name: string;
    type: string;
    similarity: number;
    filePath: string;
    signature: string;
}

export function deactivate() {}
