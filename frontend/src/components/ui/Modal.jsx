import React from 'react';
import { Dialog, DialogPanel, DialogTitle, Transition, TransitionChild } from '@headlessui/react';

export const Modal = ({ isOpen, onClose, title, children }) => {
    return (
        <Transition appear show={isOpen} as={React.Fragment}>
            <Dialog as="div" style={{ position: 'relative', zIndex: 50 }} onClose={onClose}>
                <TransitionChild
                    as={React.Fragment}
                    enter="ease-out duration-300"
                    enterFrom="opacity-0"
                    enterTo="opacity-100"
                    leave="ease-in duration-200"
                    leaveFrom="opacity-100"
                    leaveTo="opacity-0"
                >
                    <div style={{ position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)' }} />
                </TransitionChild>

                <div style={{ position: 'fixed', inset: 0, overflowY: 'auto' }}>
                    <div style={{ display: 'flex', minHeight: '100%', alignItems: 'center', justifyContent: 'center', padding: '16px', textAlign: 'center' }}>
                        <TransitionChild
                            as={React.Fragment}
                            enter="ease-out duration-300"
                            enterFrom="opacity-0 scale-95"
                            enterTo="opacity-100 scale-100"
                            leave="ease-in duration-200"
                            leaveFrom="opacity-100 scale-100"
                            leaveTo="opacity-0 scale-95"
                        >
                            <DialogPanel style={{
                                width: '100%',
                                maxWidth: '600px',
                                transform: 'scale(1)',
                                overflow: 'hidden',
                                borderRadius: '16px',
                                backgroundColor: 'var(--color-bg-surface)',
                                border: '1px solid var(--color-border)',
                                padding: '24px',
                                textAlign: 'left',
                                boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
                                transition: 'all 0.3s ease',
                                color: 'var(--color-text-primary)'
                            }}>
                                {title && (
                                    <DialogTitle
                                        as="h3"
                                        style={{ fontSize: '18px', fontWeight: '700', fontFamily: 'var(--font-display)', marginBottom: '16px' }}
                                    >
                                        {title}
                                    </DialogTitle>
                                )}
                                <div style={{ marginTop: '8px' }}>
                                    {children}
                                </div>
                            </DialogPanel>
                        </TransitionChild>
                    </div>
                </div>
            </Dialog>
        </Transition>
    );
};
