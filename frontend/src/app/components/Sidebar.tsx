import { Shield, Plus, FolderOpen, LogOut } from 'lucide-react';
import { NavLink } from 'react-router';

export function Sidebar() {
  return (
    <aside className="w-64 bg-white border-r border-gray-200 flex flex-col h-screen">
      {/* Logo Area */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-black rounded-lg flex items-center justify-center">
            <Shield className="w-6 h-6 text-white" strokeWidth={1.5} />
          </div>
          <div>
            <h1 className="font-semibold text-black">Evidence Search</h1>
            <p className="text-xs text-gray-500">RAG Engine</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4">
        <div className="space-y-1">
          <NavLink
            to="/new-case"
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                isActive
                  ? 'bg-black text-white'
                  : 'text-gray-700 hover:bg-gray-50'
              }`
            }
          >
            <Plus className="w-5 h-5" strokeWidth={2} />
            <span className="font-medium">New Case</span>
          </NavLink>

          <NavLink
            to="/past-cases"
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                isActive
                  ? 'bg-black text-white'
                  : 'text-gray-700 hover:bg-gray-50'
              }`
            }
          >
            <FolderOpen className="w-5 h-5" strokeWidth={2} />
            <span className="font-medium">Past Cases</span>
          </NavLink>
        </div>
      </nav>

      {/* User Section */}
      <div className="p-4 border-t border-gray-200">
        <div className="flex items-center gap-3 px-4 py-3">
          <div className="w-9 h-9 bg-black rounded-full flex items-center justify-center">
            <span className="text-sm text-white font-medium">JD</span>
          </div>
          <div className="flex-1">
            <p className="text-sm font-medium text-black">John Doe</p>
            <p className="text-xs text-gray-500">Investigator</p>
          </div>
          <button className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-gray-100 transition-colors">
            <LogOut className="w-4 h-4 text-gray-600" strokeWidth={2} />
          </button>
        </div>
      </div>
    </aside>
  );
}
