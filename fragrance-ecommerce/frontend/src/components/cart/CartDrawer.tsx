"use client";
import { Fragment } from "react";
import { Dialog, Transition } from "@headlessui/react";
import { XMarkIcon, MinusIcon, PlusIcon, TrashIcon } from "@heroicons/react/24/outline";
import Image from "next/image";
import Link from "next/link";
import { useCartStore } from "@/stores/cart";
import { formatPrice, getProductImage } from "@/lib/utils";

export default function CartDrawer() {
  const { isOpen, closeCart, items, removeItem, updateQuantity, total, itemCount } = useCartStore();
  const cartTotal = total();

  return (
    <Transition show={isOpen} as={Fragment}>
      <Dialog onClose={closeCart} className="relative z-50">
        <Transition.Child
          as={Fragment}
          enter="ease-in-out duration-300" enterFrom="opacity-0" enterTo="opacity-100"
          leave="ease-in-out duration-300" leaveFrom="opacity-100" leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black/40 backdrop-blur-sm" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-hidden">
          <div className="absolute inset-0 overflow-hidden">
            <div className="pointer-events-none fixed inset-y-0 right-0 flex max-w-full pl-10">
              <Transition.Child
                as={Fragment}
                enter="transform transition ease-in-out duration-300"
                enterFrom="translate-x-full" enterTo="translate-x-0"
                leave="transform transition ease-in-out duration-300"
                leaveFrom="translate-x-0" leaveTo="translate-x-full"
              >
                <Dialog.Panel className="pointer-events-auto w-screen max-w-md">
                  <div className="flex h-full flex-col bg-charcoal-100 border-l border-white/[0.08] shadow-xl">
                    <div className="flex items-center justify-between px-6 py-5 border-b border-white/[0.08]">
                      <Dialog.Title className="font-serif text-xl text-cream">
                        Shopping Bag <span className="text-sm font-sans font-normal text-white/40">({itemCount()})</span>
                      </Dialog.Title>
                      <button onClick={closeCart} className="p-2 text-cream/70 hover:text-gold-500 transition-colors">
                        <XMarkIcon className="w-5 h-5" />
                      </button>
                    </div>

                    <div className="flex-1 overflow-y-auto px-6 py-4">
                      {items.length === 0 ? (
                        <div className="flex flex-col items-center justify-center h-full text-center">
                          <p className="font-serif text-xl text-white/40 mb-2">Your bag is empty</p>
                          <p className="text-sm text-white/35 mb-8">Discover the collection</p>
                          <Link href="/products" onClick={closeCart} className="btn-primary text-xs">
                            Shop Now
                          </Link>
                        </div>
                      ) : (
                        <ul className="divide-y divide-white/[0.06]">
                          {items.map((item) => {
                            const price = item.variant?.website_price ?? item.product.website_price ?? 0;
                            return (
                              <li key={item.id} className="flex gap-4 py-5">
                                <div className="relative w-24 h-32 flex-shrink-0 bg-charcoal-300 overflow-hidden">
                                  <Image
                                    src={getProductImage(item.product)}
                                    alt={item.product.name}
                                    fill
                                    className="object-cover"
                                  />
                                </div>
                                <div className="flex-1 min-w-0">
                                  <p className="text-[10px] tracking-widest uppercase text-gold-500">
                                    {item.product.brand?.name}
                                  </p>
                                  <p className="font-serif text-sm mt-0.5 line-clamp-2 text-cream">{item.product.name}</p>
                                  {item.variant && (
                                    <p className="text-xs text-white/40 mt-0.5">{item.variant.name}</p>
                                  )}
                                  <p className="price text-sm mt-2">{formatPrice(price * item.quantity)}</p>
                                  <div className="flex items-center gap-3 mt-3">
                                    <div className="flex items-center border border-white/15">
                                      <button
                                        onClick={() => updateQuantity(item.id, item.quantity - 1)}
                                        className="p-1.5 text-cream/70 hover:bg-white/5"
                                      >
                                        <MinusIcon className="w-3 h-3" />
                                      </button>
                                      <span className="px-3 text-sm min-w-[2rem] text-center text-cream tabular-nums">{item.quantity}</span>
                                      <button
                                        onClick={() => updateQuantity(item.id, item.quantity + 1)}
                                        className="p-1.5 text-cream/70 hover:bg-white/5"
                                      >
                                        <PlusIcon className="w-3 h-3" />
                                      </button>
                                    </div>
                                    <button
                                      onClick={() => removeItem(item.id)}
                                      className="p-1.5 text-white/40 hover:text-red-400 transition-colors"
                                    >
                                      <TrashIcon className="w-4 h-4" />
                                    </button>
                                  </div>
                                </div>
                              </li>
                            );
                          })}
                        </ul>
                      )}
                    </div>

                    {items.length > 0 && (
                      <div className="border-t border-white/[0.08] px-6 py-6">
                        <div className="flex justify-between items-center mb-6">
                          <span className="text-sm text-white/50">Subtotal</span>
                          <span className="price text-lg">{formatPrice(cartTotal)}</span>
                        </div>
                        <p className="text-xs text-white/35 text-center mb-4">Shipping &amp; tax calculated at checkout</p>
                        <Link
                          href="/checkout"
                          onClick={closeCart}
                          className="btn-primary w-full text-center block"
                        >
                          Checkout
                        </Link>
                        <button onClick={closeCart} className="w-full mt-3 text-xs text-center text-white/40 hover:text-gold-500 transition-colors tracking-wider uppercase">
                          Continue Shopping
                        </button>
                      </div>
                    )}
                  </div>
                </Dialog.Panel>
              </Transition.Child>
            </div>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
}
