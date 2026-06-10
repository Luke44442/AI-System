'use client'

import { useEffect } from 'react'
import RecommendationRow from '@/components/product/RecommendationRow'
import { recommendationsApi } from '@/lib/api'
import { useRecentlyViewed } from '@/hooks/useRecentlyViewed'

export default function ProductRecommendations({ productId }: { productId: string }) {
  const { ids, track } = useRecentlyViewed()

  // Record this product as viewed (most-recent first).
  useEffect(() => { track(productId) }, [productId, track])

  const otherRecentIds = ids.filter((id) => id !== productId)

  return (
    <div className="divide-y divide-gray-100">
      <RecommendationRow
        title="Complete the Look"
        subtitle="Pieces that pair perfectly"
        load={() => recommendationsApi.completeTheLook(productId, 8)}
      />
      <RecommendationRow
        title="Frequently Bought Together"
        load={() => recommendationsApi.frequentlyBoughtTogether(productId, 4)}
      />
      <RecommendationRow
        title="You May Also Like"
        load={() => recommendationsApi.similar(productId, 8)}
      />
      {otherRecentIds.length > 0 && (
        <RecommendationRow
          title="Recently Viewed"
          load={() => recommendationsApi.recentlyViewed(otherRecentIds)}
        />
      )}
    </div>
  )
}
