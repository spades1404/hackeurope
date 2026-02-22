import { useState, useEffect } from 'react';
import { CheckCircle, AlertTriangle, Edit, X, XCircle } from 'lucide-react';
import { toast } from 'sonner';
import { proposalsApi } from '../../api';

export const CurrentTasks = ({ tasks: initialTasks }) => {
  const [tasks, setTasks] = useState(initialTasks);
  const [editingTaskId, setEditingTaskId] = useState(null);
  const [editData, setEditData] = useState({ confidence_score: 1, status: 'matched' });

  useEffect(() => {
    setTasks(initialTasks);
  }, [initialTasks]);

  const startEdit = (task) => {
    setEditingTaskId(task.match_proposal?.id);
    setEditData({ confidence_score: task.confidence_score || 1, status: 'matched' });
  };

  const cancelEdit = () => {
    setEditingTaskId(null);
  };

  const saveEdit = async () => {
    try {
      await proposalsApi.update(editingTaskId, editData);
      toast.success("Proposal updated");
      setTasks(tasks.map(t => {
        if (t.match_proposal?.id === editingTaskId) {
          return { ...t, confidence_score: editData.confidence_score, match_proposal: { ...t.match_proposal, status: editData.status } };
        }
        return t;
      }));
      setEditingTaskId(null);
    } catch (e) {
      toast.error("Failed to update proposal");
    }
  };

  const handleApprove = async (proposalId) => {
    try {
      await proposalsApi.accept(proposalId);
      setTasks(tasks.filter(t => t.match_proposal?.id !== proposalId));
      toast.success('Task approved successfully');
    } catch (e) {
      toast.error('Failed to approve task');
    }
  };

  const handleReject = async (proposalId) => {
    try {
      await proposalsApi.reject(proposalId);
      setTasks(tasks.filter(t => t.match_proposal?.id !== proposalId));
      toast.success('Task rejected');
    } catch (e) {
      toast.error('Failed to reject task');
    }
  };

  const handleFlag = async (proposalId) => {
    try {
      await proposalsApi.flag(proposalId);
      toast.warning('Task flagged for review');
    } catch (e) {
      toast.error('Failed to flag task');
    }
  };

  return (
    <div className="bg-white rounded-lg border border-[var(--tt-border)] p-6">
      <h3 className="font-semibold text-lg mb-4" style={{ color: 'var(--tt-text)' }}>
        Current Tasks — Awaiting Approval
      </h3>

      <div className="space-y-4">
        {tasks.length === 0 ? (
          <div className="text-center py-8" style={{ color: 'var(--tt-text-muted)' }}>
            <CheckCircle className="w-12 h-12 mx-auto mb-2 opacity-50" />
            <p>All tasks completed! 🎉</p>
          </div>
        ) : (
          tasks.map((task) => {
            const confidence = task.confidence_score || 0;
            let borderClass = 'border-[var(--tt-danger)] bg-[var(--tt-danger-bg)]';
            let icon = '🔴';
            if (confidence >= 0.85) {
              borderClass = 'border-[var(--tt-success)] bg-green-50/50';
              icon = '✅';
            } else if (confidence >= 0.5) {
              borderClass = 'border-[var(--tt-warning)] bg-yellow-50/50';
              icon = '⚠️';
            }

            return (
              <div
                key={task.transaction_id || Math.random()}
                className={`p-4 rounded-lg border ${borderClass}`}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-lg">{icon}</span>
                      <span className="font-semibold" style={{ color: 'var(--tt-text)' }}>
                        {task.match_proposal?.extracted_invoice?.invoice_number || 'N/A'} — {task.match_proposal?.extracted_invoice?.vendor_name || 'N/A'}
                      </span>
                      <span className="font-mono" style={{ color: 'var(--tt-text-body)' }}>
                        {task.currency === 'EUR' && '€'}
                        {task.currency === 'GBP' && '£'}
                        {task.currency === 'USD' && '$'}
                        {(task.match_proposal?.extracted_invoice?.gross_amount || 0).toLocaleString()}
                      </span>
                    </div>

                    {task.match_proposal ? (
                      <div className="text-sm space-y-1" style={{ color: 'var(--tt-text-muted)' }}>
                        <div>Matched to {task.transaction_id} — Confidence: {editingTaskId === task.match_proposal?.id ? (
                          <input
                            type="number" step="0.01" max="1" min="0"
                            value={editData.confidence_score}
                            onChange={e => setEditData({ ...editData, confidence_score: parseFloat(e.target.value) })}
                            className="border border-[var(--tt-border)] p-1 rounded bg-white w-20 text-[var(--tt-text)]"
                          />
                        ) : (
                          `${(confidence * 100).toFixed(1)}%`
                        )}</div>
                        <div className="flex flex-col gap-1 mt-2 font-medium">
                          {task.match_proposal.match_reasons?.map((reason, idx) => (
                            <span key={idx} className="flex items-center gap-1">
                              {reason.includes('Amount') ? (task.match_proposal.amount_match ? '✅' : '❌') : ''}
                              {reason.includes('Invoice date') ? (task.match_proposal.date_match ? '✅' : '❌') : ''}
                              {reason.includes('Vendor') ? (task.match_proposal.vendor_match ? '✅' : '❌') : ''}
                              {reason.includes('reference') ? (task.match_proposal.reference_match ? '✅' : '❌') : ''}
                              <span className="ml-1">{reason}</span>
                            </span>
                          ))}
                        </div>
                      </div>
                    ) : (
                      <div className="text-sm" style={{ color: 'var(--tt-text-muted)' }}>
                        {task.error || 'No matching proposal found'}
                      </div>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2 mt-4">
                  {editingTaskId === task.match_proposal?.id ? (
                    <>
                      <button onClick={saveEdit} className="px-3 py-1.5 rounded-md bg-[var(--tt-primary)] text-white text-sm font-medium hover:bg-[var(--tt-primary-dark)]">Save Overrides</button>
                      <button onClick={cancelEdit} className="px-3 py-1.5 rounded-md bg-[var(--tt-bg-alt)] text-[var(--tt-text)] text-sm font-medium border border-[var(--tt-border)] hover:bg-[var(--tt-border-light)]">Cancel</button>
                    </>
                  ) : (
                    <>
                      <button
                        onClick={() => handleApprove(task.match_proposal?.id)}
                        className="flex items-center gap-1 px-3 py-1.5 rounded-md bg-[var(--tt-success)] text-white text-sm font-medium hover:opacity-90 transition-opacity"
                      >
                        <CheckCircle className="w-4 h-4" />
                        Approve
                      </button>
                      <button
                        onClick={() => handleReject(task.match_proposal?.id)}
                        className="flex items-center gap-1 px-3 py-1.5 rounded-md bg-[var(--tt-danger)] text-white text-sm font-medium hover:opacity-90 transition-opacity"
                      >
                        <XCircle className="w-4 h-4" />
                        Reject
                      </button>
                      <button
                        onClick={() => handleFlag(task.match_proposal?.id)}
                        className="flex items-center gap-1 px-3 py-1.5 rounded-md bg-[var(--tt-warning)] text-white text-sm font-medium hover:opacity-90 transition-opacity"
                      >
                        <AlertTriangle className="w-4 h-4" />
                        Flag
                      </button>
                      <button
                        onClick={() => startEdit(task)}
                        className="flex items-center gap-1 px-3 py-1.5 rounded-md bg-[var(--tt-bg-alt)] text-[var(--tt-text)] text-sm font-medium border border-[var(--tt-border)] hover:bg-[var(--tt-border-light)] transition-colors"
                      >
                        <Edit className="w-4 h-4" />
                        Edit
                      </button>
                    </>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
